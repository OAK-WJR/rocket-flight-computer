# R11 decisions

Each decision states what was chosen, why, and its evidence label (Measured / Datasheet / Calculation / Inference,
AGENTS §2.5). The owner's standing instruction (2026-11-01 / -02) is to decide from the flight physics and the
AVA / MicoAir / LEVIA designs without intermediate questions, and to ask only where an AGENTS §2 rule itself would
change. No decision here changes an AGENTS §2 rule.

## D-R11-01 Scope: R10's circuit, new physical implementation

R11 keeps R10's netlist (commit `deb179e`, `m3_design/assembly_review/schematic.net.xml`), its part values and its
functions: the single external switch that powers and arms the board, U9's reverse / over-voltage / current-limit
front end, the RAW_ACT load switch Q120 / Q121, R134 2 Ω, Q124 with its full gate network, the continuity and bus
senses, the three identical always-on ports, the isolated camera port, four servo signals, QSPI plus microSD logging,
the buzzer, USB-C and SWD. Changes are limited to packages, case sizes, connectors, stackup, outline, placement and
copper (D-R11-02 … -07). A package change keeps the part's electrical rating at or above R10's (voltage, power,
capacitance after DC bias, pulse rating); where it cannot, the R10 package stays.
**Why:** R10's circuit went through 36 review rounds; the compactness the owner asked for is physical. Re-deciding
the circuit would reopen reviewed safety items for no size gain.

## D-R11-02 Outline 46 mm wide, as short as the parts allow (target 50 mm, ceiling 56 mm)

Not 36 × 36 mm. **Calculation (measured courtyards, `pcbnew` on both boards):** R10's courtyards total 2986 mm²,
the eight DB125 terminals 945 mm² of that, leaving about 2040 mm²; the TFBGA-100 (D-R11-04) saves about 195 mm² and
0402 passives (D-R11-06) roughly 60–90 mm² more, so about 1800–1900 mm² remain before connectors (Inference until
stage B measures it). 36 × 36 mm gives 2592 mm² over both faces: about 72 % fill before the GH ports and mounting
holes. LEVIA-H7, the routed six-layer reference, is at 45 % (1407 mm² on 2 × 39.63²). At 45–50 % R11 needs about
3800–4200 mm², i.e. 46 × 41–46 mm before edge losses. The vehicle constraint is the Ø50.8 mm coupler bore
(the parent project's `docs/VEHICLE.md`; REQUIREMENTS P1 / P2 carry it here), which allows R10's 46 mm
width; the board's cost to the vehicle is its length in the main-section stack, so width is spent first. The 30.5 mm
drone stack pattern has no use on a rocket sled.

## D-R11-03 Six layers: F / In1 GND / In2 power / In3 signal / In4 GND / B

LEVIA-H7's arrangement. Both outer signal layers sit on a solid GND (In1, In4) one thin prepreg away; In3 carries the
inner signals referenced to In4; In2 carries R10's In2 role (the rail regions). A TFBGA-100 at 0.8 mm pitch needs
the extra routing layers. The JLC stackup is named in stage B from JLC's published 6-layer table (Datasheet, URL in
the stage record). M1's "4-layer" becomes "6-layer" for R11. M3's cap counts parts plus feeder fees only, so the
PCB price is reported, not gated (as for R10).

## D-R11-04 MCU STM32H743VIH6, TFBGA-100 (JLC C964146)

Same die and peripheral set as R10's VIT6; the GPIO-to-function map stays R10's `r10_net` column, re-keyed from LQFP
pins to balls from ST DS12110 (stage A cites the page). **Supplier check (2026-11-02, JLC API):** C964146 4355 in
stock, 4043 orderable, $8.8446; R10's C114409 VIT6 is $10.7044. The courtyard is about 100 mm² against 295 mm².

## D-R11-05 Connectors: latching JST-GH for every signal port, plated wire pads for battery and pyro

| R10 | R11 | Reason |
|---|---|---|
| J410 / J420 / J440 DB125-4 | JST-GH 4-pin SM04B-GHS-TB, same pin order (1 4V8, 2 GND, 3 TXO, 4 RXI) | GPS ≤ 150 mA, radio ≤ 300 mA, AUX ≤ 100 mA on one contact each, under GH's 1 A rating (JST GH datasheet) |
| J9 camera DB125-4 | JST-GH 6-pin: two contacts for the camera supply, two for GND, then RXI, TXO | the 1 A camera allowance is 0.5 A per contact instead of 1 A on one |
| J122 servo DB125-5 | JST-GH 5-pin, same order (1–4 SERVO1–4, 5 GND) | signal only; motor power stays in the pack-star harness |
| J400 switch DB125-2 | JST-GH 2-pin | about 7 µA through the switch |
| J1 battery DB125-2 | two plated wire pads | the board's battery current includes the fire pulse |
| J121 pyro DB125-2 | two plated wire pads | fire current about 2.4 A with a 1 Ω match on a full pack and 4.2 A into a short (8.4 V / 2 Ω, R10 M3_R10), above GH's 1 A |

**Why (flight physics):** boost and vibration loads need every wired joint to be positively retained. GH latches;
LEVIA-H7's SH 1.0 does not and is rejected. A soldered wire pad has no contact to open; the harness is tied to the
sled within 20 mm of the pads (stage E procedure), as MicoAir and LEVIA do for battery leads. The e-match is never
connected at the board: the pyro pads carry a permanent pigtail to the bay's field terminal, so R10's pad check on
J121.2 moves to that terminal. The DB125s were 945 mm² and set R10's length.

## D-R11-06 Passives in 0402 where the rating allows

Every resistor and capacitor whose working voltage, dissipation and (for capacitors) capacitance after DC bias stay
within the 0402 part's rating keeps R10's value in 0402; the rest keep their R10 case or move one size down only
with a datasheet check recorded in stage A (R134, R166 and the pulse and bulk parts are expected to stay).

## D-R11-07 Copper by explicit tables; the autorouter only as a drafting aid

As R10 (D-R2-08), the build draws copper from explicit tables with no path search, and the critical nets (AGENTS §3)
are hand-routed. Freerouting (local jar) may draft non-critical signal routes offline; a draft is adopted only as a
frozen table in the repository that passes route_check's clean-routing rules (REQUIREMENTS M2). The build never runs
the autorouter.

## D-R11-08 Gate

`tools/check.sh` keeps R10's gate on the frozen R10 board and adds R11's: DRC / parity / ERC on `m3_design/r11/`,
`r11_sch_check`, metadata / models, silkscreen, `fit_check --profile r11`, `tools/check_r11.py` (R10's contract rules
re-expressed for R11's geometry, S-8 over all four inner layers), `route_check --profile r11`, the R11 fab manifest
and the gates' seeded tests. R10's netlist replay now ignores the `<tool>` version stamp: the committed netlist was
exported by KiCad 10.0.7 and this machine has 10.0.6, with no other byte different (Measured, `diff`).

## D-R11-09 Review rule

Ten lenses (docs / binding, gate, manufacturing, MCU, mechanics, parts, power, requirements, routing, safety) and one
triage verifier per round. Only real errors count: rule violations, gate misses, false documents and wrong
calculations, shown by reproducible evidence. Iteration stops after two consecutive full rounds with zero verified
real errors on the same board.

## D-R11-10 Four corner M3 supports, nylon hardware (stage B)

Supports at (3.5, 3.5), (42.5, 3.5), (3.5, 46.5) and (42.5, 46.5), 3.2 mm holes, nylon screws, nuts and washers (P2).
On a 46 × 50 mm board the unsupported spans are 39 × 43 mm between centres, shorter than any R10 span (R10: 38 × 41.8
and 38 × 40.3 with five supports on 90 mm); a fifth support would cost about 50 mm² of top and bottom keep-out in the
middle of the parts. The R10 plate model (`tools/plate_model.py`) has no r11 profile and was not run: the stiffness
claim is an Inference until stage D or the gate adds one. fit_check's corner rule (one support within 6 mm of each
corner) holds; nearest bottom envelope J430 3.55 mm (≥ 3.5), nearest top body J1.2's wire allowance 3.95 mm (≥ 3.8).

## D-R11-11 IMU pose: bottom, rotation 180, on the roll axis

U4 at B(23.0, 20.5), rotation 180 after the flip: R10's axis map is kept (+X_imu = −x_board, +Y_imu = −y_board,
+Z_imu out of the bottom face; roll = −gyro_Y; forward thrust reads −a_Y). Its centre is on x = 23 (the roll axis with
the top face on the bore axis), so the transverse lever arm is 0 mm (R10: −6 mm), z ≈ −2.06 mm as R10 (Inference).
`r11/design/r11_gate_data.json` 'imu' records it for check_r11 M-7.

## D-R11-12 Short edges: JLC panel rails, courtyards ≥ 0.5 mm from the short edges

The six GH ports sit on the short edges, mouths facing out, because a plug entering across a long edge cannot fit
the Ø50.8 mm bore (the long edges are 23 mm from the axis; a GH plug and wire need 8.7 mm). R10's M-8 (2.5 mm from
the rail-less short edges, JLC assembly terms §2.3) would cost 4 mm of length. R11 instead orders the assembly panel
with 5 mm edge rails on both short-edge sides (JLC: 5 mm tooling edges, 2 mm tooling holes, 1 mm fiducials,
https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-11-02), joined by mouse-bite tabs in the gaps between the
GH bodies, and holds courtyards ≥ 0.5 mm from the short edges (≥ 0.25 mm from the long edges). The 24 parts nearer
than 2.5 mm are recorded in `r11_gate_data.json` 'short_edge_queries' at their measured distances (M-8 DFM queries).
The panel drawing and the tab positions are stage D's (Inference until JLC's DFM accepts them).

## D-R11-13 Edge assignment

Aft edge (y = 0, the battery bay and the fin-can raceway): J400 (GH-2), J122 (GH-5 servo), J9 (GH-6 camera). Forward
edge: J420 (radio), J410 (GPS), J440 (AUX), the identical GH-4 ports together. West long edge: J1 battery pads (aft,
leads from the pack aft of the board) and J121 pyro pads beside the pyro cell (the pigtail runs forward to the
bulkhead terminal). East long edge: USB-C J3 (bench) and, on the bottom, microSD J430. Basis: stageB.md section 5.

## D-R11-14 Barometer away from heat

U5 on the bottom at B(9.0, 40.0), west-forward: ≥ 37 mm from U401 / U400 / L400, 33 mm from U402, 15 mm from U2,
10 mm from L1, 29.5 mm from U9 (centre to centre, Calculation on the placement). Its port faces the sled side;
the sled must leave it open (stage E procedure item).

## D-R11-15 Stage C infrastructure: net classes, widths, vias, family gate

Signal tracks 0.1 mm (one track between two 0.4 mm lands at 0.8 mm pitch, 0.15 mm each side), clearance 0.1 mm (JLC
multilayer 0.09 mm track / space plus 0.01, https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-11-02; the DRU
floor rule); rails from R10's width set (0.2 … 2.0 mm) sized per IPC-2152 by the family that draws them. Vias 0.4 / 0.2
(signal, BGA dog-bone), 0.45 / 0.25 and 0.6 / 0.3 mm (power), all through F → B (no blind / buried vias). `m3.kicad_pro`
gets a Default (signal) and a Power class (r11_sch.py). Each family has its own module and is gated by
`r11_stage_check.py` (DRC, unconnected never rising, route_check r11 only on pending nets). **Why:** the TFBGA-100
channels set the signal width; through vias keep JLC's standard six-layer process. Measured (kicad-cli DRC): the DRU's
0.25 mm copper-to-hole rule, not the 0.1 mm clearance, sets via spacing (0.15 mm copper gap, 0.55 mm between foreign
vias).

## D-R11-16 U1 fan-out by one frozen table

`m3_design/r11_fanout.tsv` lists every connected ball with its escape: drawn by core, an F.Cu lane, or a reserved via
site for its family; `r11_route_core.fanout_check` keeps core's vias off every reserved site. **Why:** the bottom
decoupling under the field closes most interstitial sites (stageC1.md §2), so the escapes are planned together rather
than per family. Two balls (C6, D6) are left `open` with their dog-bone sites free (stageC1.md §4).

## D-R11-17 Two placement changes for the fan-out

C19 / C20 (both 2.2 µF 16 V X5R 0603, VCAP) swap places, the south one rotated 270, so VCAP2 (E7, north of F8) uses the
north cap and VCAP1 the south one, each beside its ball's via, and the south cap's GND pad reaches R5.2. LED2 moves
0.8 mm east (26.8, 20.6) so F.Cu has room for the via of U4's GND pins 2 / 3. **Why:** with the stage-B positions the
two VCAP straps cross and U4's east GND pins had no via site clear of LED2's pads. Same parts, values and sides; fit,
courtyards and DRC re-checked in the build (Measured).

## D-R11-18 QSPI on F.Cu under U3, IMU over U4 on F.Cu

CLK, IO0, IO1 reach U3 with no via, IO3 / IO2 / NCS with two; IMU CS and MOSI run on F.Cu in the channel between LED1 /
R32 and LED2 / R33 above U4 (one via each), SCK on In3, MISO on B.Cu. **Why:** fewest layer changes on the critical
SPI / QSPI nets and their GND partners within 1.5 mm; In3 under the field stays free for the forward-to-aft nets of
the later families (servo, camera).

## D-R11-19 I2C and BARO_SDO on In3 to the barometer

The I2C pair runs on In3 north of Y1 and down the west side to vias at R12 / R13 and south of U5's pads; BARO_SDO by In3
from R64 under U5. **Why:** U5's inter-row band is closed to tracks (R10's BARO rule area), so pads 6 / 7 / 8 are
reachable only from the south, and R64 / R12 / R13 sit north and east of them; In3 crosses under U5 without blocking.
The vias under C84's can are an Inference to confirm in stage D (stageC1.md O-C1-4).

## D-R11-20 USB cluster: placement and topology

U10 rotated 270 (IN / EN aft, OUT / ILIM / FAULT forward) at (34.9, 25.1); R85 (ILIM) and R90 (FAULT pull-up) into the
B.Cu strip between U10 and D4; C28 / C83 (VBUS) onto F.Cu at J3.A4B9, east of U3; R87 / R88 (U11's USB OV divider) beside
U11.5; R7 / R8 rotated 270; TP82 onto the USB_LIMITED run (25.0, 41.15). D+ / D- on F.Cu north of U3 to J3; J3's D+ pads
joined by a loop west of the pads, the enclosed D- pad (A7) by one via and In3 back to D-'s via; D4 taps each line by one
via; VBUS's two J3 pins joined on In3; CC to B.Cu (CC2 under J3's body). **Why:** with the stage-B spots the USB support
parts sat west of core's SWD B.Cu lines (x 32.0 / 32.35) and every one of their nets had to cross them, and U10's three
signal pins faced J3. Courtyards, fit and DRC re-checked in the build (Measured).

## D-R11-21 Pyro cell re-placement

Q120 rotated 180 (sources north, facing Q121's south-row sources across the gap; gate at its west end); R120 / R119 (each
FET's own 100 k gate bias) beside each gate on F.Cu; C120 in Q120's gate island; R134 0.05 mm forward; R132 east of the
RAW_ACT run; TP120 east of R134.2 and TP122 at the south end of the Q124 gate column; Q122 / R122 / R123 / C123 south of
PE4's lane on PC1's lane; R121 onto B.Cu at the end of the ACT_GATE trunk; R126 / R127 / R128 / C126 as a gate column and
a GND column; D120 rotated 270; TP80 / TP81 / TP88 forward to y 34 (clear of Q124's fire-return vias, test-pad 1.0 mm
rule). **Why:** with both FETs at rotation 0 Q120's gate sat between the two source groups and Q121's gate between
RAW_ACT and R134, so the fire path or a gate had to take a via; PE4 (C3) and PC1 (F2) leave U1 one above the other and
their targets were in the reverse order. The fire path is now F.Cu only with no series via (AGENTS §2); S-1 … S-3c, S-5,
S-6, S-8, S-9 pass (Measured, check_r11 --only).

## D-R11-22 ACT_GATE / ACT_DRV barrels: single, with S-8 rule areas

Two ACT_GATE barrels (one per FET island) and one ACT_DRV barrel; each keeps a 1.3 mm rule area (no tracks, no fills) on
In1..In4, J121's pads 2.3 mm areas (their 2.5 mm inner rings: In1..In4 for J121.1, In2 / In3 for J121.2). **Why:**
route_check r11 has no PARALLEL_VIAS list (D-R11-08), so R10's second barrels (D-R24-02) fail track_loop / extra_vias;
the price is that check_r11 K-power's single-via-open taps Q120.4 / Q121.4 → R121.1 fail until the gate data carry an R11
entry (stageC2.md O-C2-5, owner / gate lane). S-8 Measured: nearest foreign inner copper 1.218 mm (ACT_DRV to a GND via
ring) before the pours; the rule areas keep the pours out (Inference until poured).

## D-R11-23 PE4's gate-net spacing at the TFBGA (owner deviation; corrected in stage C2b)

What the package forces: ball C3 (PE4, PYRO1_GATE_N) is 0.731 mm edge to edge from the 3V3 balls B2 and D2 (0.8 mm pitch,
0.40 mm lands, diagonal neighbours: Calculation on DS12110 Rev 8's TFBGA-100 pitch and stage A's land). What the routing
forces on this board (Inference from the copper, not a package fact): C3's two east interstitial sites (22.4, 25.6) /
(22.4, 26.4) are closed by C13 / C15's GND pads on B.Cu directly below, so PE4 has no via near the ball, and every F.Cu
exit from C3 to its targets west of U1 passes between column-2 balls, one of which is B2 or D2. The best F.Cu lane is the
row gap between C2 (GND) and D2 (3V3) with the 0.1 mm track held at the 0.1 mm clearance floor from C2: track edge to D2's
land 0.200 mm (Measured on the routed board; was 0.150 mm before stage C2b). So PYRO1_GATE_N's nearest 3V3 copper is
D2's land at 0.200 mm (track) and B2 / D2 at 0.731 mm (ball), against R10's 1.0585 mm (D-R26-04). Only a change of core's
fan-out (moving C13 / C15 off the east sites) or of the pin assignment could reach the ball-adjacency limit. Every other
PYRO1_GATE_N copper and all PYRO1_GATE / PYRO1_OUT copper keeps at least 3.105 mm from 3V3 / 3V3A on every layer, the
In2 fills included (Measured: PYRO1_GATE 3.105 mm to a 3V3A via, PYRO1_OUT 4.370 mm; J121.1's barrel keeps no inner ring
and its nearest inner fill is In2 RAW_PROTECTED at 1.10 mm, no 3V3 / 3V3A fill within 3 mm, Measured). **Why recorded:** a
3V3 bridge to PE4's net drives Q124's gate through R126 against R128 and may fire an enabled match (R10's reasoning,
Inference); it stays a deviation for the owner, as R10 D-R26-04's retained pairs.

## D-R11-24 power family split

`r11_route_power.py` draws the regulator-local control nets (U9 dV/dt / ILIM / OVLO, the R166 damper, U402 / U11 ILIM and
soft-start). The rails, the J400 / EN chain and the In2 regions wait for the placement changes listed in stageC2.md O-C2-2
(U9's west cell, L1 / C5 at U2, U400's orientation, U402's feed, PORT_4V8's path to the forward ports). **Why:** each of
them needs a part moved or rotated before any legal copper exists; drawing partial rails would only create copper to
remove.

## D-R11-25 U9's cell: EN chain on one B.Cu run, IN without a via (O-C2-2 a)

U9 (TPS25947, B.Cu) is rotated 180 so EN (pin 1) is its aft-east corner facing J400 / R165. EN runs from U9.1 north on
B.Cu to R165.2 with R81 (pull-down) and C87 (filter) tapped 1.3 mm and 2.5 mm from U9.1 (Measured on the table), so R81 / C87
sit at U9's end of the run as R10 D-R21-05 intended, and the EN chain has no via at all (R10 kept one, D-R20-01). OVLO goes
east to R83 / R82, ILIM and dV/dt west to R84 / C81. C88 sits on the IN bar's aft end: IN runs from the bar straight through
C88.1 and on B.Cu to J1.1 (0.7 mm; the bar entry 0.3 mm for 2.0 mm, a power_narrow entry) with no via on the J1.1 -> C88.1 ->
U9.5 path (check_r11 U9 IN); its In2 BAT_IN vias hang off it as stubs. OUT leaves the OUT bar's forward end to two
0.6 / 0.3 mm vias into In2 RAW_PROTECTED. J400.2 reaches R165.1 / D402.1 by one BAT_SW_RETURN barrel (D402 rotated so its
pin 1 is beside R165.1) with a 1.3 mm S-8 keep-out on In2 / In3 (1.205 mm nearest foreign inner copper, Measured); one open
barrel there leaves EN low through R81 (board off: fail-safe, Inference). TP80 moved beside J1 on the IN run. **Why:** at
rotation 0 EN faced away from R165 and crossed the OVLO / FAULT / IN / OUT exits (stageC2.md O-C2-2 a), and a via on U9 IN
would break check_r11's no-via path rule (gate_C2.md).

## D-R11-26 The bucks' switch loops, U402's feed and U401's divider (O-C2-2 b-e)

L1 rotated 180 so L1.1 (SW) faces U2: SW runs from U2.5 under U2's body between its pin rows to L1.1 (4.0 mm of track, Calculation on the table); C5 sits
over U2.5 / U2.6 (BST). U400 and L400 rotated 180: U400.5 (SW) reaches L400.1 by 2.5 mm of 0.7 mm track (Calculation on the table; the stage C2 aid had found a 12 mm detour), C402 (BST) at
U400.6, and the feedback column R401 / R404 / R400 at U400.1. U402's PORT_5V3 comes from L400.2 by an F.Cu run along the aft
strip through C430.1 (C430 moved to U402.1, R430 to U402.5); CAM_5V runs U402.6 -> C431.1 -> two vias -> B.Cu -> J9.2 / J9.1.
U401's divider R402 / R403 moved to the FB side (west), C408 to the SS side (east), R405 onto the PORT_4V8 run west of U401;
PORT_4V8 leaves U401 by two 0.6 / 0.3 mm vias into one In2 PORT_4V8 piece that runs under J3 (x 40.7-43.25, between its
shell barrels) to the forward port band, and each port pin drops into it by one 0.6 / 0.3 mm via (one piece, so K-plane
needs no links). VLOGIC: C84.1 to U11 by two vias west of U11.1, the trunk on F.Cu under C84's / L1's gap to C99 (moved to
F.Cu at U2.3) and U2; TP83 and C99 moved. **Why:** each item of stageC2.md O-C2-2 needed a part moved or rotated before legal
copper existed; the VLOGIC trunk changes side because USB_LIMITED's B.Cu run encloses U11.8.

## D-R11-27 In2 power regions, rail taps and the 3V3A / NRST / SCK layout (O-C1-3, O-C2-3)

In2 carries a 3V3 base fill (priority 0) and BAT_IN, RAW_PROTECTED, PORT_5V3, PORT_4V8 and 3V3A polygons (priority 1),
clearance 0.2 mm, solid connections, island removal on (r11_route_power.ZONES). BAT_IN takes the aft-west block, RAW the
block under U9's outputs, the west corridor to U11 and the aft band to U400, PORT_5V3 the east block, PORT_4V8 the strip
under J3 and the forward band, 3V3A a column west of NRST's In3 run (x 19.6, which lies under 3V3) and a block over U4 that
covers SCK's whole In3 run, so SCK's chain sees only 3V3A and NRST's only 3V3 (check_r11 K-region OK, K-plane OK: every
rail one piece, Measured). H1 (VDDA) reaches R164.2 by B.Cu (C24 moved north of H1, core's NRST stub shortened to it); R164.1,
D120.3 and K1's via are joined by a B.Cu 3V3 run (D120's In2 3V3 via removed from the pyro family). Every 3V3 / 3V3A / rail
pad has its own via to its region (drafted with a scratch via finder), except R89.1 (3V3), which waits for BAT_FAULT_N
(O-C2-4). Inner copper is 15.2 um (JLC06161H-3313): the narrowest current-carrying In2 neck, RAW's column at x 19.2-20.6
to U400, is 1.4 mm against gate_C2.md's 0.88 mm inner floor for 1.9 A (Calculation, the fit's Inference inputs).
**Why:** In2 is power and GND only (K-inner), and the K-region conflict of O-C1-3 needed SCK and NRST each under one net.

## D-R11-28 J1 / J121 wire pads keep no unconnected inner ring (O-C2-7)

The AWG 20 wire-pad footprint (r11_parts.py) now sets remove_unused_layers / keep_end_layers, as R10 D-R20-05: an inner
layer keeps a ring only where the pad's own net has copper there (none on R11). J121's S-8 keep-outs shrink from 2.3 to
1.75 mm (0.65 mm barrel wall + 1.0585 mm, D-R26-04's gate-net spacing, which also covers S-8's 1.0 mm). S-8 Measured on the
routed board: J121's barrels have no foreign inner copper within 1.0 mm (nearest In2 fill 1.10 mm); check_r11 S-8 OK.
**Why:** a 2.5 mm ring on four inner layers only brought foreign copper nearer to PYRO1_OUT / PYRO1_IGN.

## D-R11-29 Second barrels on single-via taps (O-C2-5)

Q120's and Q121's ACT_GATE islands each get a second barrel joined to the first on F.Cu and B.Cu ((14.6, 15.1), (13.95,
21.65)), each with its S-8 keep-out (the second Q121 barrel 1.100 mm from In3 I2C1_SDA, Measured, against 1.0 mm); U10.2,
R85.2 and the R7.2 / R8.2 island get a second GND barrel; R400.1, R82.1 / R80.1, R91.1 and the BAT_IN trunk get a second via
into their In2 region. The no-pour pairs are listed in r11_gate_data.json 'parallel_vias' (ACT_GATE x2, VLOGIC x2, CAM_5V)
with their reasons; single_open_exceptions stays empty. **Why:** check_r11 K-power fails any tap on one via (R10's
SINGLE_OPEN_TAPS) and route_check r11 now accepts listed parallel pairs (gate_C2.md).

## D-R11-30 PE4's lane moved to the C2 side of the D2 gap (D-R11-23)

PYRO1_GATE_N leaves C3 diagonally to (21.65, 26.35) and runs west at y 26.35 instead of 26.4, 0.1 mm from C2 (GND) at the
clearance floor, so D2 (3V3) gets 0.200 mm instead of 0.150 mm (Measured). **Why:** the most the row gap allows with no via
(D-R11-23 as corrected).


## D-R11-31 D4.2's GND via clear of its pad (O-C2-13)

usb's GND via beside D4.2 moves from (35.15, 30.4) (0.45 / 0.25 mm, its ring inside D4.2's mask and paste) to (35.35, 30.4)
as a 0.4 / 0.2 mm via: 0.165 mm from D4.2's pad end, its hole 0.27 mm from V_DM's ring, 0.57 mm from V_DM (GND partner)
(Calculation on the table; DRC and check_r11 K-copper OK, Measured). **Why:** K-copper failed the via in D4.2's mask
opening and paste aperture; the larger via does not fit beside V_DM.

## D-R11-32 The D-R11-10 supports pinned in the gate data (M-3)

`r11_pcb.py` holds the four corner centres as `SUPPORTS` ((3.5, 3.5), (42.5, 3.5), (3.5, 46.5), (42.5, 46.5)), stops the
build if the placement table's `@M3` rows differ, and writes them to `r11_gate_data.json` key `supports`. check_r11 M-3
OK (Measured). **Why:** M-3 failed with no pin; writing the pin from the same table it checks would let a support move
unreviewed, so the pin is a constant in the generator.

## D-R11-33 microSD pull-ups beside the SD route (placement)

R460-R464 (10 k, 3V3 pull-ups of SD_CS / MOSI / MISO / DAT1 / DAT2) move from the forward edge (x 30-34.6, y 42.4, B.Cu)
to one F.Cu column north-east of U1 (x 28.7, y 14.9 DAT1, 15.8 MISO, 16.7 MOSI, 17.6 CS, 18.5 DAT2; rotation 180, SD pad
east), between LED2 / C461 and the U400 input-cap block. Their 3V3 pads join on one F.Cu bus to one via (28.27, 19.25) in
the In2 3V3 strip between 3V3A and PORT_5V3; J430.4's 3V3 via moves from (37.405, 17.15) to (37.105, 14.25), at the pin,
so the SD runs can pass south of it under J430. **Why:** U1's SD balls (B8 / B9 / C8 / D8) are on the field's north-east
side and J430 is north-east; with the pull-ups at the forward edge every SD line but SCK had to reach both ends of the
board through the field (Calculation: about 30 mm more per line). Fit, courtyards and DRC re-checked in the build
(Measured). The SD family itself is not drawn (stageC3.md O-C3-4): the column leaves one F.Cu track between the resistor
pads and C400 / C404, so the row order and via sites are a plan, not a checked route (Inference).

## D-R11-34 VCAP1's second barrel; no site for BOOT0, VCAP2 or PA4 (O-C2-12)

U1.F8 (VCAP1) gets a second barrel at its NE interstitial site (26.4, 28.0), joined to the first (25.6, 28.0) on F.Cu
through the ball and on B.Cu, listed in `parallel_vias` (route_check and check_r11 K-power: VCAP1 OK, Measured). BOOT0
(D5), VCAP2 (E7) and PA4 (G3, LOGIC_SOURCE_ST) have no second site: every other interstitial site of D5 / E7 / G3 is
closed by a bottom decoupling pad (C20.1 at x 23.55-24.45, C16.1 at y 26.53-27.07, C17.1 / C17.2 at y 28.93-29.47; a 0.4 mm
via there overlaps the pad, Calculation on the placed pads), the one F.Cu lane out of E7 / D5 meets other dog-bones, and
(24.8, 26.4) is D6's only site. They stay K-power findings (stageC3.md O-C3-5). **Why:** R10 met the rule with second
vias in open copper (D-R24-03 / -04, D-R22-02); under the TFBGA the sites are a fan-out decision (moving C20 / C17 or the
ball assignment), not a routing one.

## D-R11-35 Sense lines: PYRO1_CONT and ARM1_SENSE_MID routed, ARM1_SENSE open (O-C2-1)

PYRO1_CONT: U1.F1 to a via at its SW site (20.0, 28.8); B.Cu north in the via-free lane x 20.4 under ball column 1 (between
the x 20.0 and x 20.8 via columns, 0.15 mm each side), diagonally north of Y1 / C25 to (16.9, 21.9); In3 to (14.0, 19.0)
under the ACT_GATE B.Cu trunk (the In3 corridor between the ACT_GATE S-8 keep-outs); B.Cu to the bank row y 20.43 (C127,
R178, R130, R129.2). ARM1_SENSE_MID: R132.2 by a via to In3, west along y 18.57 and diagonally over the banks to a via south
of R175, B.Cu into R175.1. The ARM1_SENSE bank row (C129, R180, R133, R175.2) is drawn; U1.H4 to it is not (stageC3.md
O-C3-1). S-6 / S-8 OK (Measured). **Why:** the y 18.5 In3 corridor of stageC2.md 8.3 holds; the bank-side via that
stageC2.md could not place is not needed when the line comes up beside C127 on B.Cu.

## D-R11-36 VLOGIC_SENSE and LOGIC_SOURCE_ST routed, BAT_FAULT_N open (O-C2-4)

VLOGIC_SENSE (PA6): U1.J3 down the F.Cu lane x 21.6, a via at (21.6, 32.6), B.Cu round C10 / C23 to R60.2, R61.1, C60.1.
LOGIC_SOURCE_ST (PA4): U1.G3 east along the y 28.8 row gap to a via at (23.2, 28.8), In3 through the field (x 22.8, y 26.8
north of NRST's via), south along x 18.4 and diagonally to a via south of R91 (16.23, 41.6); B.Cu to R91.2 and U11.9
beside U11 (not under it). BAT_FAULT_N (H3) and R89 are not drawn or moved (stageC3.md O-C3-1). **Why:** these are the
lanes the fan-out table reserved; PA4's single barrels are D-R11-34's finding.

## D-R11-37 Family `ports`: the wire sides and their clamps

The three GH ports are one cell translated by the port centre x0 (J420 12.4, J410 23.0, J440 33.6): TX pin 3 by F.Cu to a
via west of the cell (x0 + 0.1, 45.9), B.Cu north into the resistor's wire pad and south into the clamp; RX pin 4 to a via
between the columns (x0 + 1.25, 45.9), B.Cu north-east into its resistor and south into its clamp; each clamp's GND pad
0.625 mm to its own GND via (x, 46.45), which is also the wire vias' GND partner (0.76 / 0.83 mm). J9 (camera): each wire
pin by one via under the housing (y 3.6) to its clamp (west) and resistor; CAM_TX_WIRE reaches R101.2 along y 0.6 south of
the clamps; four GND vias (two clamp returns, two partners). check_r11 K-ports: every port clamp on the wire side within
4.5 mm (stageC3.md section 2 for the measured lengths); the only K-ports finding left is D402 (J400's clamp, the ground
family's via, O-C2-8). **Why:** the MCU sides cannot leave the field yet (stageC3.md O-C3-1); the wire cells are
independent of them and close K-ports.

## D-R11-38 Family `servo`: J122's outputs

R150-R153 (B.Cu, SERVO1-4 west to east) feed J122.1-.4 (F.Cu, east to west): each output changes layer once beside its
resistor or south of the pin row, SERVO1 / SERVO2 crossing on F.Cu under J122's housing and SERVO3 / SERVO4 on B.Cu.
**Why:** the order reverses between the resistor row and the connector; one via per net is the minimum. The MCU side
(U1.G2-K2) is open (stageC3.md O-C3-1).

## D-R11-39 Family `status` and the family order

`r11_route.FAMILIES` and `r11_build.sh` gain `status` (after `signals`, before `ground`): LEDs, buzzer and test points.
It draws LED_RED_A, LED_YEL_A, BUZZ_G and BUZZ_OUT (local, F.Cu / B.Cu, one via on BUZZ_OUT). LED_RED, LED_YEL and BUZZ_DRV
are open (stageC3.md O-C3-3). The test points need no new copper: TP80 / TP82 / TP83 / TP120 / TP122 are on their nets'
runs, TP74 / TP88 (GND) and TP81 (RAW_PROTECTED, its In2 via drawn) wait only for the ground family. **Why:** the brief
named `status` as its own family; `r11_stage_check` judges every family in `FAMILIES` order.

## D-R11-40 check_r11 K-rules fails on R10's floors (gate finding, not changed here)

check_r11 K-rules runs check_r10.k_rules with only the DRU hash patched, so R10's floors (R23-GATE-03: 0.15 mm clearance and
track, 0.5 / 0.3 mm via, 0.25 mm hole to hole, net-class clearance 0.15 mm) judge R11's D-R11-15 floors (0.1 / 0.1 mm,
0.4 / 0.2 mm vias, JLC's six-layer figures): 13 of its 14 findings. The 14th ("R11 board floor: via hole to hole" can
override "JLC pad hole to hole") comes from jlc_hole_table's later-rule test, which compares layers only and ignores the
rule's condition (A.Type == 'Via' && B.Type == 'Via', which cannot match a pad pair). Both are gate-lane items (tools/ is
not edited by the design lane); the project's rules and the board are as D-R11-15 set them (Measured: 14 findings, the
same on the C2b and C3 boards).

## D-R11-41 I2C1's nets move to PB10 / PB11 (balls J7 / K7, peripheral I2C2) — firmware binding item

The nets I2C1_SCL / I2C1_SDA keep their names and every other pin (R12, R13, U5); only the MCU ball changes: SCL from PB8
(B4) to PB10 (J7), SDA from PB9 (A4) to PB11 (K7), alternate function AF4 I2C2_SCL / I2C2_SDA (DS12110 Rev 8 Table 11
p. 91, Port B alternate functions; the page is the one R10's pin table cites for Port B). B4 / A4 become NC.
`r11_sch.R11_REPIN` carries the move into the pin table (r11_net, mode, source), the schematic (`repin`: a global label
on the new ball, a no-connect on the old) and `r11_sch_check.expected()`; the stage A gate passes (strict ERC 0, 54 / 54
seeded faults, Measured). **Firmware binding:** the barometer bus is I2C2 on PB10 / PB11. **Why:** the targets (U5,
R12, R13) are south-west; from the north row the pair walled In3 west and north of the field (stageC3.md O-C3-1), from
the south row it leaves through the south edge with the other south-going nets. **Open:** PB10 / PB11 are ROM-loader
pins (USART3; K-loader, stageC1b.md O-C1b-2).

## D-R11-42 BUZZ_DRV moves from PC14 (A1) to PB15 (G10) — firmware binding item

PB15 is a general-purpose I/O (DS12110 Rev 8 Table 9 p. 75); a push-pull output needs no alternate function, and it is not
limited to PC14's 3 mA / 2 MHz RTC-domain drive (Inference: R162 1 kOhm keeps the gate current as R10 computed). A1 is
NC. **Why:** R162 / Q123 lie south-east (44.4, 39.0); from the north-west corner ball the line had to cross the whole
field, from G10 it leaves on F.Cu through the east edge. **Open:** PB15 is a ROM-loader pin (USART1_RX, input pull-up
while the loader runs: Q123's gate may be pulled up through R162 with BOOT0 high, Inference; K-loader, O-C1b-2).

## D-R11-43 Placement for the escape plan

C17 (3V3 decoupling) to (30.3, 25.3) B.Cu under U3's north end, C21 (VDDA decoupling) to (19.0, 22.1) F.Cu over the In2
3V3A strip with its own via, R5 (BOOT0 pull-down) to (28.4, 33.9) B.Cu: their old spots under the field closed every
interstitial site of rows F-K in columns 3-6. C19.2 gets its own GND via at the site (24.0, 31.2). U13 rotated 180 so
CAM_5V enters U13.1 from C91.1 north of U13 and the corridor east of U12.6 opens; R150-R153 and R154-R157 reversed
(SERVO1 east) so each servo output runs straight to its J122 pin (no output crosses another; R153.1 was enclosed by the
old crossing). Fit, courtyards and DRC re-checked in the build (Measured). C17 / C21 now decouple through the In2 3V3 /
3V3A planes from up to about 7 mm away (Inference).

## D-R11-44 One escape plan, one table, one checker

`m3_design/r11_fanout.tsv` pins the escape of every used ball (path, via site, exit side, layer and slot on U1's
courtyard, target), `m3_design/r11_escape_check.py` proves it (one row per ball, no two exits in one slot on a layer
and side, each exit faces its target) and checks it against the copper (vias, target pads, crossings) in `r11_build.sh`.
The re-planned MCU-side copper is one frozen table per family in `m3_design/r11_escape.py`, drawn by each family module
(`core`, `usb`, `pyro`, `power`, `ports`, `servo`, `sd`, `signals`, `status`); `sd` and `signals` are new modules.
In3 under the field carries the north-going nets on ball-column lines (each line one 0.1 mm track whatever sits on the
sites), the south / east / west edges the rest; SWD leaves east. A family's `NETS` lists only the nets that pass its
gate; thirteen drawn nets and four balls stay open (stageC1b.md §5). **Why:** greedy per-family routing had walled the
field (stageC3.md O-C3-1); the plan decides every ball's channel together.

## D-R11-45 single_open_exceptions for the in-field dog-bones of PA4, BOOT0 and VCAP2

U1.G3 via (21.60, 28.80), U1.D5 via (27.20, 26.40) and U1.E7 via (24.80, 27.20) are listed in `r11_gate_data.json`
`single_open_exceptions` with their measured reasons (each ball's other interstitial sites carry another ball's escape
via or sit inside C20's pads). PA4's second via (14.65, 39.90), outside the field, stays a K-power finding to give a
second barrel (O-C1b-4).

## D-R11-46 In2 3V3 base fill: 0.12 mm clearance, 0.1 mm minimum width

`r11_route_power.zone` gives the priority-0 3V3 base fill 0.12 mm clearance and 0.1 mm minimum width; the priority-1
power regions keep 0.2 / 0.2 mm. Between two foreign vias 0.8 mm apart (the ball field's interstitial sites) the base fill
is now 0.16 mm wide (Calculation) instead of absent, so every In3 line there lies over one In2 region (check_r11
K-region OK, Measured). 0.12 mm is above the 0.1 mm DRU floor and the 0.1 mm width above JLC's 0.09 mm minimum (the
D-R11-15 sources). S-8, K-plane, K-inner and K-copper unchanged (Measured). **Why:** stageC1b.md O-C1b-3.

## D-R11-47 R89 over the In2 3V3 strip

R89 (BAT_FAULT_N's 10 k pull-up) moves from (13.4, 5.2) B.Cu, in the BAT_IN region, to (17.5, 19.3) F.Cu rotation 180,
over the In2 3V3 strip north-west of U4. R89.2 taps BAT_FAULT_N's In3 run by a via at its corner (17.30, 20.45); R89.1
reaches R11.2's 3V3 by an In3 hop. **Why:** R89.1 needs 3V3, and the BAT_IN region has none.

## D-R11-48 PA4's south via stays a single point

PA4's In3-to-B.Cu via (14.65, 39.90) has no second-barrel site: a trial at (16.05, 38.50) shorted LOGIC_ILIM's B.Cu run
and C85.2 (DRC, Measured), and the via's own surroundings (I2C vias 0.57 mm away, the 3V3 via, R86.1) leave none
closer. It is a fourth `single_open_exceptions` entry with that reason. BUZZ_DRV stays on PB15 after a trial on PD15
(G8, not a loader pin) found no escape; the K-loader allowance case for PB10 / PB11 / PB15 is stageC1b.md section 7.

## D-R11-49 Escape-first pin map (coordinator decision, 2026-11-03)

Every movable function of U1 is re-assigned by the side of the board its target lies on, then routed; the six-layer
stack stays. Fixed: PE4 (fire), PC1 (bus enable), PC0, PC5, BOOT0, NRST, PH0 / PH1, PA11 / PA12, PA13 / PA14, VCAP,
VREF and the supply balls, with their reviewed analyses. Moved (ball HEAD 33876fe -> D-R11-49; mode; DS12110 Rev 8
Table 9 for GPIO, Tables 10 / 11 for the alternate functions):

| Function (net) | Was | Now | R11 mode |
|---|---|---|---|
| Camera UART TX (CAM_MCU_TX) | PE8 / J5, UART7_TX AF7 | PB9 / A4 | UART4_TX AF8 |
| Camera UART RX (CAM_MCU_RX) | PE7 / H5, UART7_RX AF7 | PB8 / B4 | UART4_RX AF8 |
| SERVO1_MCU | PA0 / G2, TIM5_CH1 | PB7 / A5 | TIM4_CH2 AF2 |
| SERVO2_MCU | PA1 / H2, TIM5_CH2 | PA15 / A8 | TIM2_CH1 AF1 |
| SERVO3_MCU | PA2 / J2, TIM5_CH3 | PA0 / G2 | TIM5_CH1 AF2 |
| SERVO4_MCU | PA3 / K2, TIM5_CH4 | PA1 / H2 | TIM5_CH2 AF2 |
| IMU_CS | PB7 / A5 | PE3 / B3 | GPIO out, high before output mode |
| IMU_INT1 | PE1 / C4, EXTI1 | PD5 / B6 | GPIO in, pull-down, EXTI5 |
| CAM_UART_OE | PE9 / K5 | PC15 / B1 | GPIO out, low speed (PC13-15: 3 mA, 2 MHz) |
| CAM_PWR_EN | PE11 / H6 | PC14 / A1 | GPIO out, low speed |
| CAM_FAULT_N | PE12 / J6 | PC13 / A2 | GPIO in |
| CAM_5V_SENSE | PB1 / K4, ADC12_INP5 | PC2_C / E2 | ADC3_INP0 |
| LED_RED | PD5 / B6 | PB1 / K4 | GPIO out |
| LED_YEL | PD7 / D6 | PD2 / B7 | GPIO out |
| USB_FAULT_N | PD6 / C6 | PD10 / H9 | GPIO in |
| BUZZ_DRV | PB15 / G10 | PE8 / J5 | GPIO out, low before output mode |

Unchanged since D-R11-41: I2C1_SCL / SDA on PB10 / PB11 (peripheral I2C2). Now NC: PA2, PA3, PE1, PE7, PE9, PE11,
PE12, PD6, PD7, PB15 (PB0 stays NC, the AVA contract). Loader pins: PB15, PA2, PA3, PE11 and PE12 are freed; PB9
(CAM_MCU_TX) and PA15 (SERVO2_MCU) are new, with their cases in stageC1b.md section 8.

Placement: LED1 / R32 forward beside the ports, (20.6, 42.3) / (23.0, 42.3); U12 rotation 180 (MCU side faces U1); C93
to (22.6, 12.4); C21 0.15 mm west, (18.85, 22.1). Power: the 3V3A In2 block's west edge stays x 20.8; R89.1 (3V3) joins
R11.2 through a via over the 3V3A block, (18.57, 20.55), with an In2 fill keep-out of 0.5 mm radius there (no 3V3 sliver
in 3V3A's clearance ring). BOOT0 gets a second barrel at R5's end, (28.30, 33.10); D5's dog-bone (23.20, 27.20) is the
`single_open_exceptions` entry (it replaces the D-R11-45 site (27.20, 26.40), which now carries SD_MOSI's GND partner).
The board stays 46 × 50 mm. **Why:** greedy per-family escapes walled the field (stageC1b.md sections 1, 5 and 7); with
targets grouped by side every ball has an exit (count table in stageC1b.md section 8).

## D-R11-50 Family `ground`: solid In1 / In4 planes and a via for every GND pad (stage C4)

`m3_design/r11_route_ground.py` pours In1 and In4 as one GND zone each over the whole board (outline inset 0.3 mm,
priority 0, island removal always, thermal reliefs 0.25 / 0.3 mm on pads as the DRU's small-GND-pad rule) with 0.12 mm
clearance and 0.1 mm minimum width, as D-R11-46's In2 3V3 base fill, so the planes stay continuous between two vias
0.8 mm apart in the ball field. Every GND pad that had no via (stageC3.md O-C3-7, stageC1b.md O-C1b-6) gets a straight
or one-bend stub from its centre to its own via, or to a GND pad or via already joined (tables PAD_RUNS / PAD_VIAS,
frozen from a scratch drafting aid; HAND_RUNS / HAND_VIAS drawn by hand where the aid found no site). Every joint keeps
at least 135 degrees between the tracks that meet at a via or pad centre and no leg shorter than max(width, 0.2) + 0.05
mm, so route_check finds no acute angle, right angle, short segment or jog. No F.Cu / B.Cu GND pour: every GND pad has
its own path, and an outer pour at R11's 0.1 mm rules would leave pieces with one pad and no via (K-copper pour debris,
Inference). **Why:** stage C4 of r11_plan.md section 4; the planes are the K-reference planes of D-R11-03.

## D-R11-51 ARM1_SENSE on one In3 diagonal; C26.2's via moved to the ground family

ARM1_SENSE's In3 run is one diagonal (19.50, 30.90) to (11.65, 23.05) (x - y = -11.4); its bank end via moves from
(11.40, 23.05) to (11.65, 23.05). The core family's C26.2 via (18.00, 29.20), which forced the 0.15 mm jog, is removed;
C26.2 is joined by the ground family. **Why:** stageC1b.md section 8.6 (two tiny jogs and a short segment).

## D-R11-52 GPS_TX_MCU: the jog's middle run lengthened to 0.5 mm

(26.30, 38.65) - (25.45, 39.50) - (24.95, 39.50) - (24.30, 40.15) - (24.30, 43.45): the middle segment is 0.50 mm, the
offset 0.35 mm, so route_check's tiny-jog test (middle < 0.5 mm or offset < 0.25 mm) passes; a single diagonal is forced
out by C99.2 and C9.1 (stageC1b.md section 8.6). Clearances checked with the drafting aid and DRC (Measured).

## D-R11-53 SD_MOSI: straight B.Cu after the In3 via; the R46x 3V3 via moved

The In3 run stays on x 28.6 (on x 28.75 its copper edge leaves the In2 3V3 fill beside SD_CS's via (29.15, 20.75):
K-region, Measured) to its via (28.60, 19.75); B.Cu runs straight on x 28.6 to (28.60, 18.25) and diagonally to (29.80,
17.05), with no jog. For that, the R460-R464 column's 3V3 via moves from (28.27, 19.25) to (28.05, 19.22) (R464.2 -
(28.27, 19.00) - via). Still forced (Measured): 4 vias against route_check's 1 + 2 and no GND partner within 1.5 mm of
(29.80, 17.05) (stageC4.md section 4): allowlist requests to the gate lane.

## D-R11-54 CAM_RX_BUFFER keeps four vias (allowlist request)

U12.1 and R100.2 are both B.Cu pads, so route_check allows 0 + 2 vias. A two-via route exists only through In3 from the
3V3 region (y > 9.95) into the RAW_PROTECTED region (y < 9.95), which K-region forbids for a port UART net; with the In3
run held in one region the drafting router finds none, and F / B alone need four (stageC1b.md section 8.6; Measured on
the scratch board). Allowlist request to the gate lane (stageC4.md section 4).

## D-R11-55 3V3 power runs and the In2 sliver

The power family's 3V3 findings are removed: L1.2 - U2.1 runs (17.0, 37.0) - (18.1, 38.1) east with the two In2 vias
dropped straight from (19.4, 38.1) and (20.2, 38.1) (no side-by-side overlap, acute or right angle; chain detour
1.18 / 1.13, Calculation); D120.3 reaches R164.1's pad by the shortest B.Cu run; R12.2 and R164.1 turn by 45 degrees.
PORT_5V3's In2 polygon starts at y 10.15 (was 10.30), so the 3V3 base fill no longer leaves a 0.138 mm sliver between it
and RAW_PROTECTED (route_check pour_sliver, Measured). The USB family's C86.2 via sits on the F.Cu C83.2 - C28.2 strap's
bend node (36.56, 33.80) (route_check via_on_track).

## D-R11-56 VLOGIC trunk through C6.1; LOGIC_SOURCE_ST's escape ends at R91.2

The F.Cu VLOGIC trunk turns at (15.6, 39.0) through C6.1's centre and back to y 39.35 at (18.05, 39.35); C6.1's TP83
branch leaves from inside the pad straight to its via. This frees (16.40, 39.00) for the only GND via of C85.2 / R86.2
(D-R11-58). LOGIC_SOURCE_ST's escape B.Cu run ends at R91.2 instead of running a second path to U11.9 beside the power
family's run (a duplicate loop route_check listed as a leftover).

## D-R11-57 Placement and escape changes for the last GND pads

R103 and R155 rotate 90 -> 270 (B.Cu), so their GND pads face free copper: R103.2 to its via (20.50, 12.03), R155.2
south to R105.2. CAM_IO_3V3 reaches R103.1 by (19.97, 10.80); SERVO2_MCU's two B.Cu runs end inside R155.1 from the north
and from the south-east (with a 45-degree corner at (20.6, 7.5)). CAM_TX_BUFFER's B.Cu corner moves from (24.30, 6.25) -
(26.50, 4.05) to (24.30, 5.35) - (25.60, 4.05), so D121.2 gets its via (24.80, 5.60). U4.6 / U4.7's run gets a node at
(21.20, 21.85) for a second barrel (21.20, 22.50).

## D-R11-58 Second barrels and five single_open_exceptions

check_r11 K-power's single-via-open taps: second barrels for U400.4, R401.2, R403.2, R81.2, R83.2 (ground family
SECOND_RUNS), U4.6 / U4.7, U9.8 tied to R84.2 by B.Cu and C87.2 tied to R81.2's run. No legal site exists for R86.2
(with C85.2), R88.2, R430.2 (two entries) and U402.2: five `single_open_exceptions` entries in `r11_gate_data.json` with
the measured reasons (drafting-aid scans on the scratch board). K-power OK (Measured).

## D-R11-59 K-reference open items (not changed here)

On the poured board K-reference finds 869 samples (Measured): 621 on NRST's B.Cu run and 3 on HSE_OUT's, over the S-8
keep-out of the ACT_DRV barrel (15.40, 29.70) on In4 (pre-existing routes, now visible); 245 at copper edges of critical
runs that sit exactly at the 0.25 mm hole clearance from a foreign via, where the plane's antipad ends (with a 0.2 mm
inner-layer plane hole clearance in a scratch DRU copy those 245 vanish, Measured). Owner of the fix: the NRST / ACT_DRV
re-plan (design) and the plane antipad rule (gate lane, `m3.kicad_dru` is pinned). stageC4.md section 6.
