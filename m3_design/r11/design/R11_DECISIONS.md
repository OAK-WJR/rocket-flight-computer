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
