# R11 stage E fix pass (2026-11-04)

Follows stageD2.md; decisions D-R11-85 … D-R11-88 in `R11_DECISIONS.md`. Nothing is committed or ordered. Labels
(AGENTS §2.5): **Measured** = read from the CAD or a tool run on it; **Calculation** = arithmetic on CAD copper and
datasheet values; **Simulation** = the numerical hot-plug model; **Inference** = anything resting on an unmeasured or
estimated input. No physical test was run. Coordinates are board mm (x east, y forward from the aft edge).

## 1. Result

Board `m3_design/r11/m3.kicad_pcb` SHA-256 `3bb832721a77c50900bd5133f57c63a35c81c908ade76626a12e9a42580cefc5`, built
twice from the final tree by `m3_design/r11_build.sh` with the same hash (Measured). The board and `m3_design/r11/fab/`
are staged in git (not committed). On it (Measured): DRC 0 violations, 0 unconnected, 0 parity, ERC 0; r11_sch_check
OK (218 parts, 55 / 55 seeded faults caught); check_r11 every rule OK, the new K-neighbours included; route_check r11
0 failing, 3 allowlisted, 0 stale, 375 instances in all categories; `tools/test_r11_check.py` 50 tests OK with
`R11_BOARD_REQUIRED=1`; 218 footprints, 1320 track segments, 386 vias. `tools/check.sh` exit status: section 6.

| Stage E finding | Fix | Decision |
|---|---|---|
| Ball B3 (PE3, IMU_CS, push-pull, idle high) beside PE4's ball C3 | IMU_CS to PB9; B3, B4 and G2 NC; camera UART, IMU_INT1 and servos 3 / 4 re-pinned; check_r11 K-neighbours | D-R11-85 |
| PC2_C (TT_a, 4.0 V absolute maximum, 0 mA injection) reached by CAM_5V on R105 open | four-resistor divider, ratio 1 / 11.2 | D-R11-86 |
| Record errors (stageC5, stageC1b, D-R11-84, r11_fab.sh, D-R11-29 / -42 / -48 / -81, D-R11-23's scope) | corrected | D-R11-87 |

## 2. Gate-drive neighbours and re-pins (D-R11-85)

Every ball within one pitch (0.8 mm, diagonals included) of C3 (PE4, PYRO1_GATE_N) and F2 (PC1, ACT_EN_MCU) on the
board as built (Measured; check_r11 K-neighbours):

| Ball | Round C3 (PE4) | Round F2 (PC1) |
|---|---|---|
| B2 / D2 | 3V3 (row-1 supply, D-R11-23 exception) | — |
| C2 | GND | — |
| B3, B4, C4, D3, D4 | NC | — |
| E1 | — | NRST: open-drain reset with an internal pull-up; bridged, ACT_EN ≤ 0.20 V (Calculation / Inference) |
| E2 | — | PC2_C CAM_5V_SENSE: analog input; bridged, ACT_EN ≤ 0.40 V (Calculation / Inference) |
| E3, F3, G2 | — | NC |
| F1 | — | PC0 PYRO1_CONT: analog divider; bridged, ACT_EN ≤ 0.38 V (Calculation / Inference) |
| G1 | — | GND |
| G3 | — | PA4 LOGIC_SOURCE_ST: open drain with a 10k pull-up, low on battery; bridged on USB, ACT_EN ≤ 0.51 V (Calculation / Inference) |

None of the four PC1 neighbours has a push-pull high state under the firmware rules; each bridged figure is below the
AO3400A's 0.65 V minimum threshold (Inference: datasheet minimum, no bench read). Re-pins (pin_table `r11_net`):

| Function | Was | Now |
|---|---|---|
| IMU_CS | PE3 (B3) | PB9 (A4), GPIO output, init high; ROM-loader case stageC1b.md §9 |
| Camera UART | UART4 PB9 TX (A4) / PB8 RX (B4) | USART2 PD5 TX (B6) / PD6 RX (C6), AF7 |
| IMU_INT1 | PD6 (C6), EXTI6 | PD3 (C7), EXTI3 |
| SERVO3 / SERVO4 | PA0 (G2) TIM5_CH1 / PA1 (H2) TIM5_CH2 | PA1 (H2) TIM5_CH2 / PA2 (J2) TIM5_CH3 |
| PE3, PB8, PA0 | used (B3, B4, G2) | NC |

EXTI lines in use stay one per line (check_r11 K-exti). The loader list adds PB9 (I2C1_SDA, held high by R11) and PA2
(USART2_TX, R10's servo case) (stageC1b.md §9, Inference). PE4's nearest driven-signal copper is QSPI_NCS's via at
0.866 mm (Measured). CAM_MCU_RX's dog-bone via (24.8, 26.4) has no legal GND site within 1.5 mm (r11_gnd_spots,
nearest 1.6 mm, Measured) and is the third route_check allowlist entry; its second via (23.2, 24.8) has a 0.3 / 0.15
GND partner at (22.4, 24.75).

## 3. PC2_C divider (D-R11-86)

R104 5.1k + R107 5.1k (net CAM_5V_DIV) over R105 2k ∥ R106 2k, C94 10 nF: ratio 0.08929 (Calculation). One resistor
open or shorted: at most 0.1639 × CAM_5V, so ≤ 0.92 V at 5.6 V, ≤ 1.60 V with U400 also failed (9.77 V), ≤ 3.26 V at
D8's 19.9 V clamp (Calculation, nominal values; tolerance and pad leakage not included). Nominal reading at 5.456 V:
0.487 V (Calculation). Hot-plug (Simulation / Inference) re-run: 2304 / 2304 required cases pass with figures identical
to stageD2.md §3; `stageD_budget.json` figures unchanged (Calculation / Inference).

## 4. Safety spacing (Measured on `3bb83272…`)

S-8 nearest foreign inner copper 1.012 mm (unchanged). PYRO1_GATE_N to 3V3 0.200 mm (D2's land), PYRO1_GATE 3.106 mm,
PYRO1_OUT 4.370 mm, ACT gate 4.085 mm from 3V3 / 3V3A (unchanged). PYRO1_OUT to GND surface pair 0.175 mm (owner row 3).

## 5. Fabrication, cost and stock

`FAB_NET=1 m3_design/r11_fab.sh`: JLC BOM 75 lines, 206 placed parts, CPL 81 top + 120 bottom (+ 5 placement-only),
paste 348 top / 323 bottom, Gerber zip 16 files, manifest bound (Measured). Cost 2026-11-04T01:15:03Z: parts $56.85 +
75 codes × $1.53 / 5 = $79.80 per board against the $84.41 cap. Stock 2026-11-04T01:13:45Z: U9 C3662793 18 / −94,
U4 C51931514 4 / −3, U2 C780769 56 / −2876 (stock / orderable; orderable an Inference about JLC's field).

## 6. Gate

`tools/check.sh` with the board and fab package staged: exit 0 (Measured, 2026-11-04). Its first run failed two
`tools/test_route_check.py` tests that pinned the r11 allowlist to two entries; they now expect D-R11-85's CAM_MCU_RX
entry (85 tests OK), and the second run passed.
