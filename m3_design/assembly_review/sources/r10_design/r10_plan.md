# R10 plan: a leaner board, informed by BPS.space AVA

Status: draft plan, owner direction of 2026-10-26. Nothing here changes R9: M3-ASSY-R9 (board `4f841a0e…`, branch
`m3-assy-r9`, commit `ac9ebba`, owner-accepted 2026-10-25) stays the current board and the fallback until R10 exists and
is accepted. Branch `m3-assy-r10` starts from R9's tip.

## 1. Basis

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
| 1 | Battery-live to armed copper ≥ **1.5 mm** (R9: 2.5 mm; R8: 1.0 mm), inner plan-view variant ≥ 1.65 mm (R9: 2.65). Every other pyro rule unchanged: A–H, the strict pad rules, P-3, P-6, P-7, LC-1. | enables #2 | Still ≥ 10× the IPC clearance and above rule H's 1.2 mm solder-bridge pairs. |
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
- `tools/check_r9.py` → `check_r10.py`: K-power-pyro's 2.5 / 2.65 mm become 1.5 / 1.65 mm; the R-rules lose the GNSS
  chain if §3 is adopted; M-7's IMU map is re-derived if U4 moves. `m3.kicad_dru` and `tools/route_check.py` gain an r10
  profile.
- A new firmware board binding (AGENTS §3).

## 5. Expected result and process

Estimated: items 1–4 plus the GPS port free about 500 mm² of parts, enough for roughly 88–92 mm of length at 46 mm width
(Inference until placement is tried); item 5 or 6 would go further. Process as R9: generators rebuild the board
reproducibly, `tools/check.sh` gates every step, and independent review passes run until two consecutive passes find
no Critical or Major, then the owner accepts the deviation list.
