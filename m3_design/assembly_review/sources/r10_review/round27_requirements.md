# R10 round 27 — requirements lens

- Target commit `816038c`; board SHA-256 `a0ec075e…2e733c` before and after (unchanged).
- Totals (real errors only): **0 Critical / 0 Major / 1 Minor.**

## Findings

### R27-REQUIREMENTS-01 (doc, Minor): the J410 / J420 / J440 schematic pin names reverse the UART direction

- **What is wrong.** All three port terminals use the embedded symbol `M3:CameraTerminal`. Its pin names are visible on
  the sheet:
  - pin 1 "5V OUT";
  - pin 3 "RX FROM CAMERA TX";
  - pin 4 "TX TO CAMERA RX".
- **What the board actually does.** On every port, pin 3 is the board's TX:
  - J410.3 = GPS_TX_WIRE ← R441 ← PD8 (USART3_TX);
  - J420.3 ← R451 ← PB13 (UART5_TX);
  - J440.3 ← R471 ← PC6 (USART6_TX).

  Pin 4 is the board's RX, and pin 1 is PORT_4V8 (4.792 V).
- **What it contradicts.**
  - REQUIREMENTS F10: "1:4V8, 2:GND, 3:TXO, 4:RXI … the module's RX goes on pin 3".
  - The same sheet's own note: "3 board TX, 4 board RX".
- **Evidence.**
  - Lines 115–179 of `telemetry.kicad_sch` define the symbol; the three instances are at lines 586, 1078 and 2466.
  - The kicad-cli PDF, page 15, prints "RX_FROM_CAMERA_TX" next to GPS_TX_WIRE, RADIO_TX_WIRE and AUX_TX_WIRE.
  - The copper, the PCB pads and the silkscreen (3:TXO, 4:RXI, 1:4V8) are correct. The symbol is also correct for J9.
- **Fix.** Give the three ports their own symbol with pin names 4V8 / GND / TXO / RXI, regenerate the schematic, re-run
  ERC and parity, and assert the pin names in `sch_check`. The board does not change.

## Fix verification

| Change | Measurement | Verdict |
|---|---|---|
| D-R26-01 | J440.3 / J440.4 join F.Cu and B.Cu; GND vias at (7.4,16.5) and (7.4,20.0) are 1.500 mm away; pads 3 / 4 of the 4-position terminal drop their unused inner rings; route_check r10 reports 0 failing on a copy; a seed moving the via 0.2 mm fails `critical_via_no_gnd` at 1.7 mm | confirmed |
| D-R26-02 | PYRO1_OUT to 3V3 / 3V3A ≥ 1.040 mm on every layer (B.Cu, R164.2); its barrels are ≥ 1.061 mm from the In2 3V3 pour | confirmed |
| D-R26-03 | Independent worst-corner EN model reproduces every figure: 8.07 ms single drop-out, 7.50 ms late block, 1.1295 V at 7 ms, holds down to 5.65 V, 1.088 / 1.095 V for 8 ms every 50 ms, 19.6 / 14.8 / 4.5 % trip fractions, pack 5.96 V for a 10 ms drop-out | confirmed |
| D-R26-04 | PYRO1_GATE / _N to 3V3 / 3V3A ≥ 1.059 mm | confirmed |

## Observations (not counted)

13 observations; the full list is in the JSON.

- **F4 / F6 consistency.** F4 and F6 agree on the 5.71 V four-stall point (7.4 − 11.246 A × 0.15 Ω). The 3 × 4 ms
  figures in F6 are for a single burst; the repeated train goes lower, so the statement stays true.
- **M2 plated-pin audit.**
  - J440.3 and J440.4 are the only critical signal pins that change layer through a plated barrel.
  - J400.2 is an AUD-2 slow net and J1.1 is power.
- **P3.** Its "28–37 g" boost-load range is flight 2's envelope rounded. Flight 1's range starts at 25.5 g.
- **VEHICLE.md-based figures.** The board-position stack (35.4, 79.4–83.4 and the 32 mm margin) and the shroud range
  reproduce.
- **Other reproduced figures.** The envelope temperatures, log size, landing g, port power, bleed time and cost all
  reproduce.
- **Board-to-requirement map.** Holes, outline, connector poses and pin nets, the D402 tap (4.114 mm, GND via
  0.700 mm), the gate networks, the dividers, the F7 width exceptions, the silkscreen sizes and C84's absence from the
  JLC BOM all match their requirements.

## Coverage limits

- Datasheets were not re-read.
- The hinge moment and the flight envelope were not re-simulated.
- P2's wire room was not re-measured against the 3D model.
- check.sh was not run, as the brief requires.
