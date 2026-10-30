# R10 vehicle integration handoff

The separately owned `../../docs/VEHICLE.md` candidate entry still describes
removed R10 hardware. This handoff supplies its replacement facts without
editing that worktree. Preserve the accepted R9 entry. The exact current PCB,
review and build binding is in [R10_VALIDATION.md](R10_VALIDATION.md); R10 remains
unaccepted and no physical fit is claimed.

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
remain unqualified. The optional 100 g/D5 model leaves only 0.274 mm below C431
at h4; h3.5 predicts overlap. This is an inference, not a physical result.

Complete maximum DB125 bodies/tails are modeled. The bare-bore OQ-1 benchmark
is 5.003012 mm at every wire face against the accepted 4.95 mm floor, only
0.053012 mm margin. It is not a ferrule/bend/tool-envelope qualification.
DB125 accepts 28-16 AWG; verify actual leads, 4-5 mm strip, ferrules, screw
access and retention. Its maximum body height is 8.90 mm and tail is
3.50 +/-0.30 mm. Stake all seven terminals, including J400.

J430 is the bottom hinged Molex microSD socket at (24,24.3). The current fit
check covers the closed socket/card allocation only. Open it unpowered with
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

Current source/qualification details: [M3_R10.md](M3_R10.md),
[ORDERING.md section 8](ORDERING.md),
and the maker-linked `sources/r10_design/parts_qualification.md`. Apply the parent
mirror update only within its separately authorized repository workflow.
