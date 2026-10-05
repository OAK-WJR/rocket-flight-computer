# M3-ASSY-R3 design: GNSS removal, 46 × 193 mm, cost-down, bench firmware

Status: design approved by the owner in conversation. Implementation follows
`docs/superpowers/plans/2026-10-05-m3-assy-r3-hardware.md` (part A) and
`docs/superpowers/plans/2026-10-05-m3-assy-r3-bench-firmware.md` (part B).

## 1. Why

- The GNSS module is dropped from the vehicle.
- The board must fit the main-section electronics bay. Measured in the Onshape CAD
  (`../../docs/VEHICLE.md` in the parent project), the bay floor is the bulkplate top at
  joint − 44.6 mm and the nose-shoulder base is at joint + 550 mm (595 mm free). The stack
  from the bulkplate up is: 2S battery bay ~80 mm, leads ~15 mm, **this board**, eyebolt
  nut and charge wiring ~25 mm, recovery ~260 mm (estimate). The board may be at most
  214 mm long with zero slack.
- Cost: R2 is ≈ $125–135 per board all-in for a 5-board JLC PCBA order (live JLC prices,
  2026-10-05). The SAM-M10Q alone is $22.82 and needs Global Sourcing.

## 2. Decisions (owner, 2026-10-05)

| Item | Decision |
|---|---|
| GNSS | Removed: U6, C33, C34, GPS_TX/GPS_RX, its 3V3A branch, its keep-out |
| Length | **46 × 193 mm**, the most robust option: only GNSS copper is deleted, no verified copper is re-routed. ~21 mm of bay slack remains |
| Barometer | MS5611 stays (no MS5607 swap) |
| Cost target | Parts ≤ $50/board, ≤ 30 extended JLC lines, ≤ $75/board all-in at 5 boards (before shipping/tax). Owner confirms the all-in number with a JLC cart quote; nothing is ordered |
| Robustness | No loss of function or margin. Swaps must be same-or-better spec in the same footprint/land pattern. Never swapped: 0.1 % threshold resistors, pyro FETs and gate networks, R134/R135, TVS/clamps, U1, U3, U4, U5 |
| Flight firmware | Out of scope |
| Bench firmware | In scope (part B), including B5 bench actuation test image |

## 3. Part A — hardware M3-ASSY-R3

A1. Remove the GNSS from schematic and PCB. MCU pins that carried GPS_TX/GPS_RX become
unconnected and get no-connect flags.

A2. Board outline 46.0 × 193.0 mm (corner radius as R2). Board y = 0 stays the battery (J1)
end. The forward M3 pair moves from y = 234 to y = 189 (x = 4 and 42); the other six M3
holes and both zip-tie holes stay. All tracks, vias and footprints aft of the cut are
untouched; zones are clipped to the new outline and refilled. The servo header J122 stays
78 mm from the aft edge (≥ 70 mm needed so plugged servo housings sit in the Ø54.6 bore,
not the Ø50.8 coupler).

A3. BOM cost-down to ≤ 30 extended lines and ≤ $50 parts/board, by same-footprint
equal-or-better swaps onto JLC Basic parts (MLCC swaps checked for effective capacitance at
the operating DC bias), and by merging duplicate LCSC codes for identical parts.

A4–A5. Every line JLC-stocked for 5 boards; no consigned or Global Sourcing part.

A6. Gates: `tools/check.sh` all zero; `m3_design/check_actuators.py` OK;
`quality_audit` PASS; `m3_design/sim_r2/run.py` passes (actuator band unchanged);
`tools/export_fab.py` reports no missing LCSC code and no unverified CPL rotation;
`tools/jlc_stock.py --boards 5` short: none; new `tools/jlc_cost.py` shows the targets met.

A7. Docs: STATUS.md, AGENTS.md §1, README.md, docs/ORDERING.md, a design record
`docs/M3_R3.md` (cut, GNSS removal, swaps with evidence, bay cross-section), and
`m3_firmware/pins_r3.json`.

## 4. Part B — bench firmware for R3 (not flight firmware)

B1. Arm GNU Toolchain 15.2.rel1 installed at the path `build.py` expects; an R3 board
binding created from `assembly_binding.py` (new hash and netlist review, never a hash edit).

B2. Bench diagnostic firmware v0.9 for R3: GNSS removed; LED_RED on PE8; PE3/PE6 driven
low; VLOGIC/V3V3 on ADC3; RAW_ACT (PB0), CAM_5V (PB1), PYRO1/2_CONT (PC0/PC1),
ARM1/2_SENSE (PC5/PC4) and PULLPIN (PC14) read and logged. No output is ever driven in
this image except LEDs and sentinels.

B3. Plug-out self-test: classifies each pyro channel as good igniter / open / shorted FET
from the ratiometric thresholds of `m3_design/sim_r2/RESULTS.md` §E.

B4. `diagnostics/` host tools rebound to R3.

B5. Separate bench-test image (never the diagnostics image): servo sweep and hold-at-stall
(TIM5, 333 Hz), buzzer tone, single 20 ms pyro pulse per channel into a dummy load. Pyro
requires a two-step USB arm → confirm within a short window, ARM plug sensed on that
channel's bus, continuity in the good-igniter band, and battery present; one channel at a
time; servos quiet during the pulse; any USB disconnect, timeout or reset disarms. All
outputs default off.

## 5. Research results that revise the targets (2026-10-05)

- **Length:** 193 mm is legal. The binding clearance is the M3 washer at (4,189) against the
  J3 USB-C courtyard, 1.075 mm. The shortest legal length is 191.925 mm. The recipe
  was tested on a scratch copy: DRC, unconnected, parity and ERC all 0; audit OK;
  `check_actuators` OK.
- **Cost (A3/A4):** the targets cannot be met without breaking the robustness rule.
  - Only two same-footprint swaps pass (C1591 → C14663, C22548 → C21190).
  - The floor is **47 extended LCSC codes** and parts of **$55.02 per board** at 5 boards
    ($58.87 including JLC minimums and attrition, INFERENCE from the API fields).
  - Fees at 5 boards, from JLC's price table updated 2026-09-09:
    - Economic PCBA feeder fee: $3.07 per extended code.
    - Bare-PCB live quote: $65.01 for 5 boards (ENIG, 1 oz inner).
  - All-in is therefore ≈ $95–100 per board, against ≈ $130 for R2.
  - Getting closer to $75 needs owner-approved relaxations. Examples: hand-solder the
    THT connectors (−5 codes), or a 12 pF crystal from the Basic library with new load
    caps (needs a gain-margin check).
  - The revised acceptance target is parts ≤ $56 and ≤ 47 extended codes at 5 boards.
- **Stock (A5):** U4 ICM-45686 (C22459454) shows JLC stock 0 on 2026-10-05 (1,023 on
  2026-09-28). U4 is protected, so it goes through JLC Global Sourcing or consignment.
  Everything else is in stock.
- **3V3A filter:** C33 (100 nF) and C34 (22 µF) also sat on 3V3A (VREF+). After removal,
  3V3A keeps C10 and C11 (2 × 22 µF), C22 (1 µF) and four 100 nF caps. My estimate (INFERENCE,
  not simulated): the L2 LC corner moves from about 9 kHz to about 11 kHz, with slightly
  higher Q. At the same time the GNSS load (tens of mA) goes away. ADC noise on 3V3A should be
  checked at bring-up with the v0.9 image.
- **Firmware:** the R1-era build chain cannot run (missing reference PDFs and checker
  modules, R1 hash). Part B builds a new, self-contained `--board r3` chain.
- **B5:** it conflicts with FMEA F-14, `pyro_may_fire()` and the LIFTOFF latch. It is a
  separate image under an owner-approved bench exemption. PA5 = TIM8_CH1N (AF3) was
  confirmed from ST pin data.

## 6. What is verified where

CAD gates, software tests and simulation are reported separately from physical tests, as
AGENTS.md requires. No R3 board is built in this work; physical bring-up uses the v0.9 and
B5 images later.
