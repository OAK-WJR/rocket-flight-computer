# R10 plan: a leaner board, informed by BPS.space AVA

**Historical completion before the new circuit changes (2026-10-28):** full rounds 9/10 are clean on the original and Minor-fix targets; final PCB`b337fe63…` is frozen. R10_VALIDATION contains the complete current deviation list; owner acceptance/OQ-3, procurement, process and physical/firmware qualifications remain pending. The single-switch/AUD/GAP amendments below supersede original hardware descriptions.

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

Current D-R17-01 uses the explicit pad-energy worksheet and full-charge formula;
the old generic2.6/4 Ah examples are retired. D-R17-02 requires future user-flash
BOOT_ADD0/boot-setting readback and reset-entry acceptance with no e-match;
BOOT0 low alone does not exclude ROM. No option bytes or R10 firmware were
programmed/read here. D-R17-03 retains1.1 mm U5 model/cover engineering allocation
while correcting the maker package height to1.0 mm +0/-0.10; D-R17-04 requires
canonical fabrication-manifest evidence. No CAD,model or circuit-generator change.

Historical starting plan: owner direction of 2026-10-26. Nothing here changes R9: M3-ASSY-R9 (board `4f841a0e…`, branch
`m3-assy-r9`, commit `ac9ebba`, owner-accepted 2026-10-25) stays the current board and the fallback until R10 exists and
is accepted. Branch `m3-assy-r10` starts from R9's tip.

## 1. Basis

- **Inspiration: AVA.** R10 takes BPS.space's AVA as its reference design. Where a choice is open, look at AVA first
  for component sizes and packages, general layout (processor in the middle, I/O on the edges, passives on the back)
  and scope (what lives on the board and what goes off it), and for routing where its images show it. The best
  images are listed in the parent repository's `reports/AVA board layout images.md`. Use AVA as the starting point,
  not the rule: AGENTS §2's safety constraints and this plan's adopted changes still govern.
- **Connector policy (owner, 2026-10-26): two families, not one.** JST GH (keyed, latching) for every signal
  connector: GPS, spare UARTs, camera, switch, pull-pin. One screw-terminal family, 3.5 mm pitch where the current
  allows it, for wires that carry current or get changed in the field: igniter, ARM, battery. The servo header stays
  2.54 mm, because the servos come with JR plugs. A single family can't do both: GH pins are rated about 1 A, too
  little for the battery and servo current, and screw terminals are bulky and grip thin signal wires poorly.
- **AVA comparison.** BPS.space's AVA flight computer is about 47.5 × 99 mm, essentially R9's area (46 × 102 mm), with
  more I/O on it: 3.5 mm screw terminals for every wire, a bulk capacitor on the back, cameras switched by a transistor,
  big servos powered off the board, the flight radio and its antenna off the board. The images, sizes and revisions are
  in the parent repository's `reports/AVA board layout images.md`. Owner direction: where AVA omits a part or uses a
  smaller one, R10 may do the same, as long as the safety requirements in AGENTS §2 hold.
- **Where R9's area goes** (part courtyards, both sides, 3,135 mm²): power input, protection and USB 30 %, GNSS and
  radio 18.5 %, MCU 12 %, camera supply 11 %, pyro 10.5 %, servo switch and outputs 10.5 %, the rest 7 %. The largest
  parts: U1 296 mm², J1 248, U30 152, C84 150, U31 137, J121 / J124 113 each, J30 / J31 101 each, J3 97, C121 91.
- **Pyro spacing has no physics floor near R9's values.** Air cannot break down below about 330 V (Paschen minimum), and
  IPC-2221B Table 6-1 asks for about 0.05–0.13 mm between conductors at 0–15 V. R7 / R8's rules A–H (0.3–1.0 mm) and
  R9's battery-live rule (2.5 mm, owner decision 2 of R9) are single-fault margins (solder bridge, loose strand, debris,
  condensation, PCB defect) protecting the one hard requirement: the ARM plug is a complete break of the pyro bus
  (F8, AGENTS §2.1). The gap that matters most is inside J124, between RAW and BUS1.
- **Hold-up study** (C84; 7.4 → 3.5 V on VLOGIC, η 0.85, −20 % capacitor tolerance, the two 22 µF ceramics included;
  loads from `sources/r7_review/pass1_electrical.md` §4.1, MCU at 200 MHz, all peripherals on, DS12110 Table 120):
  R9 rides through a battery-lead break for 7.0 ms hot (MCU Tj 85 °C; 5.7 ms at −20 %) with the radio receiving and
  4–5 ms while it transmits. Holding 10 ms hot needs about 600 µF with everything on and 450 µF with only the MCU, IMU
  and flash held; slowing the MCU to about 64 MHz during the dropout (Inference: dynamic current scaled from the 25 °C
  figure) brings it to about 270 µF. Firmware shedding needs no hardware: VLOGIC_SENSE (R60 / R61 / C60, τ ≈ 90 µs) on
  PC2_C feeds an ADC analog watchdog, and the radio's NRST (PE9) is MCU-driven.

## 2. Adopted changes (owner, 2026-10-26)

| # | Change | Area freed (estimate) | Notes |
|---|---|---|---|
| 1 | **No pyro-specific spacing rules** (owner, 2026-10-26): drop the battery-live rule (R9: 2.5 mm), rules A–H, the strict pad rules and P-3 / P-6 / P-7; pyro copper uses the board default clearance (0.15 mm, already above IPC-2221B's ~0.1 mm at 0–15 V). The AGENTS §2 hard rules stay, and so do the functional pyro requirements (the ARM plug as a complete break, gates defined off in reset, no fire at power-up or reset, sense dividers that are safe after one resistor fault) and the 2 Ω shorted-igniter limit. | enables #2 and denser placement | Accepted loss: one defect (solder bridge, strand, debris) that bridges a default gap could join RAW to the armed bus. The terminals' own pitch keeps their pads ~1.5 mm apart; bench gates (ORDERING §5) and inspection remain the check. |
| 2 | J121 / J124 become **3.5 mm-pitch 2-position screw terminals** (AVA's size), black, ARM / IGN legends kept, wires entering from −x. | ~100 mm² for both | Pick a JLC-stocked part rated ≥ 8 A; measure J124's RAW–BUS1 copper gap ≥ 1.5 mm on its real land before adopting. |
| 3 | **Split J1**: battery on a 2-position 5.08 mm terminal (≥ 15 A), the external power switch on a keyed 2-pin locking connector (JST PH like J123, or GH). | ~100 mm² | The switch contact carries about 7 µA (470 kΩ each side, since R4), so it needs no power terminal; a battery lead can no longer go into the switch terminal (F9). F8's "green 4-pin battery/switch terminal" text changes. |
| 4 | **C84 → 470 µF / 25 V, 8 × 10 mm polymer** (C121's part, C46550466), and F6 gains firmware load shedding (ADC watchdog on VLOGIC_SENSE → radio held in reset, flash writes paused, MCU clock down, LEDs and buzzer off). | ~58 mm², 2.6 mm less height | +42 % capacitance, one BOM line fewer. Ride-through hot: about 14.5 ms (11.7 ms at −20 %) with shedding, about 10 ms without. R9's 35 V C84 was a stock substitute for a 25 V part (ORDERING), and VLOGIC never exceeds U9's ~10 V OVLO. The C121 part has no maker datasheet: verify it on the bench or pick a datasheet-backed 8 mm part. |
| 5 | **Camera supply, check first**: if the RunCam Split 4 V3 runs from 2S directly, feed it from RAW_PROTECTED through U7 alone and drop U8 / L3 and the parts that only serve them; keep the UART back-feed protection. | ~150–250 mm² | Depends on the camera's input range (not yet checked). |
| 6 | **Servo power off the board, owner to decide**: power the servos from the pack through the harness, keep only the signal lines (as AVA does for big servos). | ~190 mm² | Removes Q120 / Q121, C121 and the 7.7 A copper, but also the board's servo-power switch and its failsafe sequence (F6). Not adopted unless the owner accepts that loss. |

Items 1–4 are low risk and free about 260 mm²; 5 and 6 add up to about 440 mm² more.

## 3. Open decision: an external GPS on a UART port

The order sheet's GPS, the HGLRC M100 Mini (u-blox M10, L1, 15 × 15 × 5.2 mm, 3.3–5 V, 115200 baud, SH1.0-4P
VCC / GND / TX / RX), is bought for the MicoAir H743. R9 cannot use it: R9 carries its own MAX-F10S and needs an active
antenna on J30. R10 could instead carry a GPS port and use the same module (or a bigger-patch M10 module) as the MicoAir.

- **Board side:** one spare UART on a 4- or 6-pin JST GH (positive latch for launch vibration; an SH-to-GH lead adapts
  the M100's cable), 3V3 through a current-limited load switch so firmware can shed it in a dropout, ESD and series
  resistors on TX / RX. A Pixhawk-style GH-6 GPS pinout (5 V, TX, RX, SCL, SDA, GND) would fit most drone GPS modules but
  needs a 5 V supply; 3V3 suits the M100 Mini.
- **Removed:** U30, J30, the antenna-bias limiter, the GNSS ESD and pi network and their strip copper: about 300 mm² of
  parts, and the west half of the RF strip (about 23 × 22 mm) opens up for other parts. Net of the new port, roughly
  230 mm² of parts and perhaps 5–10 mm of board length after repacking (Inference).
- **Given up:** the L5 band (little use for finding a rocket under a parachute, per the parent repository's GPS
  research), and the antenna's free placement on coax. The module's patch sits wherever its cable reaches and should face
  out through a non-conductive section. The velocity limit (about 500 m/s) is the same u-blox limit either way, and both
  need the dynamic model sent at every boot (no flash on either).
- **Gained:** the same GPS works on the MicoAir and on R10, the GPS sits away from the 22 dBm radio, and the module is
  cheap and swappable.
- **Same question for the radio (larger):** a UART port could also host the LR900-F air unit already on the order, and
  removing U31 and J31 would take the whole RF strip (aft 22 mm) off the board. It reverses the owner's 2026-10-15
  "radio and GPS on the board" decision, the LR900-F's default channels fall partly outside the US 902–928 MHz band and
  must be configured, and its link is a closed protocol (fine for transparent telemetry). Not adopted.

Recommendation: adopt the external GPS port for R10 and keep the on-board radio; decide the radio separately.

## 4. Requirement and gate changes to make with R10

- REQUIREMENTS F8 (terminal description; the battery-live figure), F9 (J1 split), F6 (load shedding, the new
  ride-through), F10 (GPS on a port, if §3 is adopted), P1 (length target), M2 (R10 deviation list).
- `tools/check_r9.py` → `check_r10.py`: K-power-pyro and the pyro spacing checks (rules A–H, strict pad rules, P-3 / P-6 / P-7) are dropped; the functional pyro checks (check_actuators, the ARM-break netlist checks) stay; the R-rules lose the GNSS
  chain if §3 is adopted; M-7's IMU map is re-derived if U4 moves. `m3.kicad_dru` and `tools/route_check.py` gain an r10
  profile.
- A new firmware board binding (AGENTS §3).

## 5. Expected result and process

Estimated: items 1–4 plus the GPS port free about 500 mm² of parts, enough for roughly 88–92 mm of length at 46 mm width
(Inference until placement is tried); item 5 or 6 would go further. Process as R9: generators rebuild the board
reproducibly, `tools/check.sh` gates every step, and independent review passes run until two consecutive passes find
no Critical or Major, then the owner accepts the deviation list.

## 6. Owner decisions, second round (2026-10-26)

The owner answered the plan's open items on 2026-10-26. These replace §2 items 5 and 6 and §3's recommendation.

| # | Decision | What it means for the board |
|---|---|---|
| O1 | **External GPS on a JST GH UART port** (§3 adopted). | Remove U30, J30, the antenna-bias limiter, the GNSS ESD and pi network and their strip copper. Add a GH 4-pin GPS port with 3V3 through a current-limited load switch the MCU can turn off, ESD on the port lines and series resistors on TX / RX. The HGLRC M100 Mini (3.3–5 V, 115200 baud, SH1.0-4P) connects through an SH-to-GH lead. |
| O2 | **External radio on a JST GH UART port** (this reverses the 2026-10-15 "radio on the board" decision). | Remove U31, J31 and the rest of the RF strip, so the board has no RF copper, no SMA jacks and no aft overhang. Add a GH 4-pin radio port for the MicoAir LR900-F air unit: 5 V DC on its GH port, about 200 mA average while transmitting at 27 dBm, 3.3 V UART, GH 4-pin ([MicoAir](https://micoair.com/radio_telemetry_lr900f/); figures from the reseller listing, to be checked against MicoAir's manual or by bench measurement). Its 5 V goes through a current-limited load switch the MCU can turn off. The uplink still can never arm or fire a pyro: no radio net may touch pyro, arming or actuator copper. The LR900-F's channels must be set inside 902–928 MHz (firmware and setup, not the board). |
| O3 | **Servo power off the board** (§2 item 6 adopted). | Remove C121, C150, C151 and the 7.7 A copper. The servos are powered from the pack through the harness. The board keeps the four signal lines with their series resistors, pull-downs and clamp. Accepted loss: the board can no longer switch servo power, so F6's "tab to neutral on reset" no longer has a board-level means and becomes a harness and servo matter. The deviation list must say so. |
| O4 | **Camera: a small 5 V regulator** in place of R9's camera supply block (U7, U8, L3 and their parts), not a direct feed from 2S. | RunCam's manual says "DC 5–20V (Non-direct power supply from battery, powered directly with battery will generate surges and burn the camera)" (`docs/SIMULATION.md` item 20), so the camera stays on a regulated 5 V. Use one compact buck (first candidate: AP63205WU-7, the 5 V sibling of U2's AP63203; verify against the maker's datasheet and JLC stock). Keep the camera UART back-feed protection (U12 / U13). |

## 7. Build decisions that follow (agent defaults; review may change them with a recorded basis)

- **Pyro bus source (AGENTS §2.2).** The pyro bus must still come "after the load switch (RAW), never straight from the
  battery". With the servos gone, Q120 / Q121 and their gate network stay as the **pyro-bus load switch** feeding RAW_ACT,
  which now serves J124.2 and the RAW_ACT sense only. Size the copper for the fire pulse: the R134 2 Ω limit gives about
  4.2 A at 8.4 V for at most 20 ms. Smaller FETs are allowed only with a verified datasheet and JLC stock. The pyro bus
  must not be fed from RAW_PROTECTED: U9's 3.96 A minimum limit is below the shorted-igniter current, so a shorted igniter
  would brown out the logic.
- **One 5 V rail** from the new buck feeds the camera port and the radio port, each through its own current-limited switch.
  The GPS port runs on 3V3 through its own switch. Each switch has an MCU enable and a fault flag. The first candidate is
  TPS2553DBVR, U10's part, which is already verified. F6's load shedding turns these switches off.
- **Servo header:** keep J122 (3 × 4, 2.54 mm) so JR plugs seat. The signal row and the GND row are connected; the middle
  (+) row has no connection, and the harness brings servo power to it. The silkscreen says so.
- **J1 split:** the battery goes on a 2-position screw terminal from the same 3.5 mm family as J121 / J124, if its rating
  covers about 6 A peak (logic plus a fire pulse); otherwise it goes on a 5.08 mm terminal. The external switch goes on a
  keyed JST GH 2-pin.
- **J123 (pull-pin):** JST PH becomes JST GH 2-pin (connector policy).
- **C84:** becomes the 470 µF / 25 V 8 × 10 mm polymer (C46550466). C121 itself is removed (O3).
- **MCU pins:** reuse the freed pins with each alternate function checked against DS12110. GPS on USART6 (PC6 TX, PC7 RX,
  as the MAX-F10S used). Radio on a UART that is not a system-bootloader port (first candidate UART4, PD0 RX / PD1 TX).
  The port enables and fault flags go on freed GPIOs (PD14, PD15, PE9, PD9, …).
- **Layout (AVA as reference):** the board is 46 mm wide. Make it as short as the parts allow, and expect well under R9's
  102 mm now that the RF strip is gone. Put U1 in the middle with the IMU next to it, the connectors on the edges (the
  screw terminals on one long edge, the GH ports grouped on an edge, J122 at an end), the passives on the back where
  possible, and four corner M3 holes. Simplicity and cleanness come first: short direct routes, few vias, no detours,
  a solid ground. VEHICLE.md's bore (Ø50.8 mm) and height limits apply; update its board entry once R10 has an outline.

## 8. Owner decisions, third round (2026-10-26, answering review round 1's R1-01 / R1-02 / R1-03)

| # | Decision |
|---|---|
| O5 | **Port supplies:** one small buck at about 5.3 V feeds the camera port (RunCam ≥ 5 V). A small LDO of about 4.8 V runs off that rail and feeds both the radio port (LR900 4.5–5 V) and the GPS port (M100 Mini 3.3–5 V). Each port keeps its own current-limited, MCU-switched load switch. This replaces §7's single 5 V rail and O1's 3V3 GPS supply. The exact set points, parts and tolerance budget (at the module input, after switch and harness losses) are for the implementation to qualify against the maker datasheets. |
| O6 | **Servo return:** the harness runs each servo's − wire straight to the pack, alongside its + wire. J122's GND row stays connected to board GND as the signal reference only. The residual share of motor return current through the board, in parallel with the harness, must be bounded by calculation and listed. The board carries no designed servo current. |


## 9. Current arming amendment (owner, 2026-10-28)

The later "Single screw switch for power and arming" decision in R10_DECISIONS supersedes references above to
J124, an ARM link and its fuse. J124 is removed; RAW_ACT is the common post-Q120/Q121 pyro bus. J400 connects one
external screw switch for power and pad arming. PC1 independently enables the load switch through R122 and Q122;
PE4 commands Q124. Both default off in reset. The power switch is turned on last and off first, only on the rail;
firmware must detect launch using the accelerometer and barometer before firing. Bench work uses USB with the pack disconnected or the e-match disconnected. USB or an independently powered port can keep logic alive with the switch open, so attach
an e-match only with every back-feed source disconnected. This accepted loss of a powered physical break does not
change the gate networks, single-resistor sense protection, post-load-switch feed or independent Blue Jay backup.
Implementation and evidence: D-SS-01 / D-SS-02 and R10_VALIDATION's single-switch pass.


## 10. Audit implementation supersession (2026-10-28)

After the committed single-switch pass `73af96b`, AUD-1…AUD-10 / GAP-1…GAP-5 are implemented as recorded in
R10_DECISIONS D-AUD-01…D-AUD-10 and D-GAP-01…D-GAP-05. The earlier plan's J123 / pull-pin, separate ARM link,
GPS/radio IO LDOs, selected probe pads and 1.0 mm fire-only tracks are historical at this boundary. Keep C443 /
C453 as main 3V3 TXU VCCB bypasses, as required by the maker. Adopt the smaller AONR21357 pair and the existing
1 µF / 25 V C29936 metric 0603 land for C120 (D-AUD-01a); allow ≥100 ms load-switch settling before bus checks. U401's two specified in-pad thermal vias
require filled/capped planar VIPPO; C84 is manually fitted after both reflows. The narrowed slow-return and
review-only drawing scopes cite AUD-2 / AUD-10; fast-return and electrical/manufacturing checks remain blocking.
No preparation pass earns full-round credit. Rebuild, check to zero, prove byte equality, export and bind the fab
package, request a supervisor commit, then start ten fresh independent lenses in round 9.


## Current circuit-only pass and hand-over (supervisor Steers1–2,2026-10-28)

Implement always-on GPS/radio, retained switched/isolated camera, SPI3 hinged
microSD alongside QSPI, sole RAW_ACT divider/direct PC0/PC5 ADCs, and DB125 for
all wired connections. R10_DECISIONS "Requirements audit2" narrows the inherited
gates/margins and selects MJG J-Tek with1.125 A current qualification floor.
No safety§2 change. Generate a connected DRC-clean board through the generators,
prove check.sh0 and byte reproducibility, request supervisor commit, then stop.
The separate layout agent owns the ten AVA follow-up changes, symmetry/cleanup,
then fresh full rounds starting11 until two consecutive clean on the same committed
board, and the final current-board deviation inventory. Rounds9/10 are historical;
this circuit pass earns no review credit. Every commit still requires check.sh0.
