# M3-ASSY-R2 — verification record (2026-09-27)

This record answers three questions for the current board:
1. Does it meet the requirements?
2. Where is it redundant, and where is it not?
3. Is every footprint, pinout and part number right?

It is CAD, datasheet and simulation evidence only. **No board has been built or measured.**

## 1. Requirements

The governing requirements are the original brief as recorded in `ROCKET_FC_FROZEN_DESIGN.md` §1, the table in `STATUS.md`, the functions in `AGENTS.md` §1 and the safety rules in `AGENTS.md` §2. Items of the original brief that were dropped are dropped with a written reason in the frozen design: microSD, ADXL375, LoRa, LSE, RGB LED, BOOT/reset buttons, and the 40 × 85 mm size. None was dropped silently.

| Requirement | Status on R2 | Evidence |
|---|---|---|
| One board, 2S supply, switch, reverse / over-voltage / current protection, logic hold-up | Implemented | `STATUS.md`, `tools/check.sh` |
| STM32H743, IMU, barometer, QSPI log, GNSS, USB, SWD, camera terminal | Implemented; U1 pin map verified pad by pad | §3 below |
| Four servos, actuator switch | Implemented, simulated | `m3_design/sim_r2` (A, F) |
| Dual pyro, single deploy, independent fuses, complete arming break, continuity / arm sense | Implemented, netlist contract, simulated | `m3_design/check_actuators.py`, sim B–E |
| Pull-pin, buzzer, indicators | Implemented, pull-pin chafe simulated | sim G |
| Commercial backup altimeter fully isolated | By ruling (2026-09-25); nothing on the board | `M3_ACTUATOR_MERGE.md` §1 |
| Safety rule 1: the ARM plug is a complete break | Holds. With the plug out, no copper, part or test point joins RAW_ACT to a bus | `check_actuators.py` rule 1 |
| Safety rule 2: pyro bus after the load switch | Holds. The buses are fed only from RAW_ACT, which is the drain of Q121 | rule 3 |
| Safety rule 4: gate pull-down, series R and gate-source C, off in reset | Holds | rule 4; sim D |
| Manufacturing package | BOM, CPL and Gerbers generated; every line has an LCSC code | `tools/export_fab.py` |

## 2. Redundancy

**Independent per channel:**
- arming-plug fuse and fused bus (FMEA H-5);
- arm sense;
- series current limiter R134 / R135;
- igniter terminal position;
- AON7524 and its gate network;
- continuity divider;
- cold pull-up.

A shorted igniter on one channel no longer affects the other channel or the logic supply (sim C: ≤ 4.1 A, BAT_IN ≥ 5.69 V).

**Shared by both channels** (single-string on the board, accepted in `FMEA_REDUNDANCY.md` §8.2 / V-10). The only backstop is the independent commercial altimeter:

| Shared item | Failure that takes out both channels | Detectable before flight? |
|---|---|---|
| Battery, J1, battery lead, in-line 15 A fuse | Open or flat | Yes (voltage, load step) |
| D8 SMBJ9.0CA | Shorts, which blows the in-line fuse | Yes (board dead) |
| Q120 / Q121 / Q122 actuator switch | Open means no RAW_ACT | Yes (RAW_ACT_SENSE) |
| RAW_ACT net: C121, C150, C151, servo harness | Short means the in-line fuse blows and the whole vehicle is dead | Only if present at power-up; a chafed servo lead in flight is not |
| ARM plug body and J120 | Plug falls out | Yes (ARMx_SENSE); retention is mechanical |
| MCU, firmware, 3V3 / VLOGIC chain, HSE, baro and IMU for apogee | Any single failure | Partly (self-test); FMEA V-1…V-6 |
| PE4 / PE5 adjacent pins | A solder bridge fires both channels together | Yes (H-1 cold test); harmless under single deploy |

**Not made redundant on purpose** (`FMEA_REDUNDANCY.md` §3.3): a second barometer, second IMU, second MCU or buck, or a separate pyro battery.

## 3. Footprints, pinouts, part numbers

All 99 BOM lines / 205 positions were checked against manufacturer datasheets in five groups. Every ISSUE found was fixed in this revision.

| Group | Result | Fixed in this revision |
|---|---|---|
| U1 STM32H743VIT6, 100 pins (ST DS12110 Rev 5, Table 8 and AF tables) | 100/100 OK: pin names, power pins, VCAP, AF of every function, ADC channel and voltage limits, LQFP100 land | — |
| Power ICs and magnetics (AP63203, AP63200, TPS259570, TPS259470L, TPS2553, TPS2121, TPS70933, L1–L3, D8, D9, C84, C121) | 12 OK, 1 ISSUE | C84 had no polarity mark on the top side; added a "+". L1/L2 3D model height was 1.9 mm; set to the real 3.0 mm |
| Signal ICs (W25Q128JVSIQ, ICM-45686, MS5611, SAM-M10Q, TXU0202, Y1, USBLC6, USB-C, LEDs) | 8 OK, 2 ISSUE | BOOT0 ran between the MS5611 pads, against TE p.16 "do not route tracks between pads"; it was rerouted outside the sensor (0/45/90° segments, 4 vias). U12 had no pin-1 mark; added one |
| Actuator discretes and connectors (AON6403, AO3400A, AON7524, BAT54A/S, SRV05-4, 1N5819WS, MLT-8530, DB128V, headers, CRM2512) | 10 OK, 2 ISSUE | The R134/R135 land was the generic 2512; it now uses the Bourns CRM2512 recommended land (2.45 × 3.7 mm pads, 7.6 mm overall), with the parts moved to x 23.6 / y 60.6 and 56.35. The AON7524 3D model was rotated 180°; its pin-1 mark now matches pad 1 |
| Passives (38 lines) | 35 OK, 3 ISSUE | R84 got its LCSC code (C705743). R9 moved to C25915 (UNI-ROYAL 0402WGF6201TCE; the old MPN has zero stock). R86 went from 80 k to **80.6 k** 0.1 % C861568: 80 k was not orderable, and U11's current limit moves by −0.75 %, which is inside the TPS2121's own ILIM tolerance |

**Kept deliberately, with a reason:**
- **U3 must stay W25Q128JV-IQ.** The IQ variant ships with QE fixed at 1, so /WP and /HOLD are data pins and need no pull-ups (Winbond §7.1.4); this closes FMEA H-3 / V-13. An IM variant would reopen the problem.
- The AON6403 land is the generic DFN5x6, not AOS PO-00044. It still covers every lead and the paddle.
- The L1/L2 land differs from Sunlord's recommendation but covers the terminals.
- SRV05-4 row spacing is 2.30 mm against Semtech's 2.50 mm; acceptable.
- U8 is set to 5.25 V on purpose (camera rail).

**Stock to confirm when ordering.** LCSC showed zero stock for these, and JLC pages list them without a stock figure:
- AP63200WU-7 (C2071868)
- SRP5030TA-100M (C3223923)
- 25SVPF330M (C178367)
- R70 (C861207), which has low stock.

## 4. FMEA hardware items (H-1 … H-10) on R2

| Item | Status |
|---|---|
| H-1 cold pull-up + BAT54A | Done (10 k, sim E) |
| H-2 separated gates + sentinels | Done |
| H-3 QSPI /WP /HOLD pull-ups | Not needed: W25Q128JV-IQ (QE fixed 1) |
| H-4 VBUS_SENSE pull-down | Done (R110 of the divider) |
| H-5 two fused buses | Done |
| H-6 physical form / reachability of the ARM plug (V-18) | **Owner decision open.** This is vehicle harness and mechanics, not the board |
| H-7 switch wetting current | **Not changed on the board.** TI requires ≥ 350 kΩ from IN to EN/UVLO for reverse-polarity safety (TPS25947 abs-max note 2), so the contact carries about 6.6 µA. Requirement: use a sealed reed / magnetic switch or a switch rated for dry-circuit use (gold contacts) |
| H-8 TVS on pyro drains | Not adopted, with reason (`M3_ACTUATOR_MERGE.md` §2.2) |
| H-9 gate-source capacitor on the load switch | Done (C120 2.2 µF) |
| H-10 BAT54S pull-pin clamp | Done |

## 5. Firmware requirements the hardware relies on

R2 firmware does not exist yet. These are hardware-derived rules, in addition to `FMEA_REDUNDANCY.md` §5:
1. Every pyro fire pulse ends after **20 ms**. This is what protects R134/R135 when an igniter is shorted.
2. Flight state (phase and armed state) survives an MCU reset (FMEA V-2).
3. Channel 2 fires 2.0 s after channel 1 regardless of channel 1's continuity (single deploy, FMEA V-7).
4. Drive PE3 and PE6 low permanently (sentinels).
5. Read VLOGIC_SENSE and V3V3_SENSE on **ADC3** (PC2_C / PC3_C reach only ADC3 unless the analog switch is closed).
6. Evaluate the plug-out self-test ratiometrically (VREF+ = 3V3A). The thresholds come from `m3_design/sim_r2/RESULTS.md` §E.
7. Do not run v0.8.1 on R2.

## 6. How to re-check

```sh
bash tools/check.sh                    # DRC / unconnected / parity / ERC = 0, metadata / 3D audit
python3 m3_design/check_actuators.py   # safety contract from the PCB copper netlist
python3 m3_design/sim_r2/run.py        # SPICE suite (needs ngspice)
```
