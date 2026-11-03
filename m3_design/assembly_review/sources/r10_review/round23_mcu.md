# R10 round 23: MCU lens (Claude), firmware bring-up obligations

- Target commit `c70d261`.
- Board SHA-256 before and after: `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1` (unchanged).
- **Totals: 0 Critical, 0 Major, 4 Minor.** Machine-readable version: `round23_mcu.json`. That file also carries the 27-row rule inventory.

## Findings

| ID | Sev | Title | Key evidence |
|---|---|---|---|
| R23-MCU-01 | Minor | The R10 rule list omits the board-tied option-byte, supply, clock and USB settings that its other rules presuppose | **Option bytes.** Only BOOT_ADD0 is named. "Loader jump only before IWDG starts" needs IWDG1_SW = software start, which is not stated (FMEA §2.2 requires it). BOR_LEV is not stated (FMEA F-3; DS12110 Rev 8 Table 126 p217: BOR1 falls at 1.95–2.06 V). SWAP_BANK, IO_HSLV and RDP are not stated. **Supply and clock.** No PWR_CR3 LDO rule (VCAP caps only, no external VCORE) and no VOS for the 200 MHz clock (Table 122 pp214-215: VOS3 HCLK ≤ 100 MHz). No PLL limits (Table 147 p239: input 2–16 MHz, VCO 192–960 MHz) and no CSS / HSE timeout (FMEA F-2), with HSE on single vias (22.00, 49.10) and (24.69, 45.50). **USB.** PA9 OTG_FS_VBUS is NC (Table 9 p80), so VBUS sensing must be overridden (Inference: RM0433 not read). |
| R23-MCU-02 | Minor | BOOT0's only pull-down and both VCAP capacitors each hang on one via, outside SINGLE_OPEN_TAPS and unrecorded | BOOT0: U1.94 → via (13.80, 45.60) → R5 (B.Cu). VCAP1: U1.48 → via (29.25, 38.00) → C19. VCAP2: U1.73 → via (18.00, 37.30) → C20. No other copper on any of the three. An open BOOT0 via → possible ROM boot at the next reset: primary recovery silent, but no fire (PC1 / PE4 analog with R123 / R127; that BOOT0 floats is an Inference, since DS12110 Table 157 p246 gives no BOOT0 pull). An open VCAP via leaves one 2.2 µF (Table 124 p216). By contrast, R123, R127 and R128 sit on F.Cu with no via. |
| R23-MCU-03 | Minor | round22_alternates.md claims a 1.6× scaling error for FS_XL_HG 010 on the LSM6DSV80X; the datasheet and ST's driver contradict it | DS14764 Rev 1 Table 3 p12: ±80 g is 3.904 mg/LSB, the same as the ISM's and the 320X's 010 (±128 g, 3.904 mg/LSB, Table 3 p12 of each). ST's `lsm6dsv80x_from_fs80_to_mg` also uses ×3.904. So 010 scales correctly on all three parts and only clips at ±80 g on the 80X, which is still ≥ F2's ±64 g. "001 only" stays safe but rests on a wrong reason. Also, ST's ISM driver maps `256g = 0x3`, which is Reserved per DS15034 Table 150 p93; the 001 / 010 rule avoids it. |
| R23-MCU-04 | Minor | Binding obligation 29 calls PB1 a TT_a pin | DS12110 Rev 8 Table 9 p70 gives PB1 as TT_u (USB option, Table 8 p63). The sheet note already says TT_u. Text only. |

Round 22 comparison (read after writing the above): none of these four findings was in round 22. Its one finding, R22-MCU-01, is fixed (D-R22-03).

## Boot and reset

- **BOOT0.** R5 (10 kΩ) pulls it down through one via (R23-MCU-02). BOOT_ADD0 must be read back; the rule is stated.
- **Safety pins in reset.** Each is held off by external copper with no via:
  - PC1: R123 2 kΩ at Q122;
  - PE4: R127 1 kΩ at the pin and R128 10 kΩ / C126 at Q124;
  - PC14: R163 10 kΩ on the buzzer gate (the PC14-side via does not matter);
  - port TX pins: high-Z at reset.
- **Trace pins.** PE4 also carries TRACED1 / TIM15_CH1N and PC1 TRACED0 / RTC_TAMP3 / WKUP5 (Table 9 p67, Tables 12 p93 / 14 p95). The lock and trace rules cover them.
- **LSE.** The LSEON rule is backed by Table 9 note 1 p88: the oscillator function survives non-POR resets.
- **Reset state wording.** DS12110 Table 8 p63 says I/Os are "floating inputs during and after reset". "Analog" as the MODER reset value comes from RM0433, which was not read here, so it is an Inference. Both states are high-Z with no pull, so the safety argument holds either way.

## Clocks and analog

- **HSE.** 25 MHz with gm = 0.49 mA/V against a Gmcrit maximum of 1.5 mA/V (Table 141 p234; NDK ESR ≤ 50 Ω; C0 + CL taken as 10 pF, an Inference). A 200 MHz PLL setting is feasible (Calculation).
- **VCAP.** 2.2 µF ±20 %, ESR < 100 mΩ (Table 124 p216). The operating C and ESR remain open qualification items, as already recorded.
- **VREF+ / VREFBUF.** VREF+ and VDDA are both on 3V3A. The SVD reset value of VREFBUF_CSR is 0x2 (HIZ = 1). The pull-down mode row is still second-hand (AN5690 via a search summary), so it remains an Inference.
- **ADC map.** PC0 ADC123_INP10, PC5 ADC12_INP8, PA6 ADC12_INP3 and PB1 ADC12_INP5 (Table 9 pp67-70). VREFIN_CAL is at 0x1FF1E860 (Table 128 p219). The VBAT ratio Q = 4 ±10 % (Table 192 p293).
- **IWDG.** 960 / 33.6 kHz = 28.571 ms and 960 / 29.4 kHz = 32.653 ms (Table 146 p238).

## U4 alternates (DS15034, DS14623, DS14764; ST -pid drivers)

- **WHO_AM_I.** 0x73 on all three (pp66 / 66 / 55), so firmware cannot tell them apart.
- **ISM6HG256X and LSM6DSV320X.** All 279 typedef'd registers in ST's headers have identical addresses and bit layouts. These include IF_CFG, INT1_CTRL, CTRL1–CTRL10, CTRL7 INT1_DRDY_XL_HG, CTRL1_XL_HG and HG_FUNCTIONS_ENABLE.
- **LSM6DSV80X.** It differs only in the OIS / EIS / IF2 bits.
- **Codes and sensitivities shared by all three:**
  - FS_G 101 = ±4000 dps (140 mdps/LSB);
  - FS_XL 11 = ±16 g;
  - the same high-g ODR codes;
  - FS_XL_HG 001 = ±64 g at 1.952 mg/LSB;
  - FS_XL_HG 010 = 3.904 mg/LSB.
- **Interrupts and timing.** IF_CFG defaults to push-pull, active high, and INT1 defaults to "output forced to ground", so PE1 with its pull-down works for all three. SPI ≤ 10 MHz and the 40 ms gyro turn-on are the same on all three.
- **Pins 10 / 11.** NC on the 80X (with a fixed pull-up, Table 22 p43) and open on the board, so they are compatible.
- **Answer.** "001 / 010 only" is enough for one driver to serve the ISM and the 320X. "001 only" is right but not necessary on the 80X (R23-MCU-03).

## Fix verification

| Item | Verdict |
|---|---|
| D-R22 (no copper change: the board hash is equal at ec8cb98 and c70d261; the Gerbers differ only in timestamps) | Confirmed |
| D-R22-03 (diagnostics note: 0.496 / 0.89 / 1.81 V) | Confirmed |
| D-R22-02 (PA6 / PA4 / R91 taps present, firmware plausibility rule) | Confirmed (path uniqueness not re-run) |
| D-R21-03 sensors note | Confirmed |
| D-R19-11 IMU rule | Confirmed |
| D-R19-13 VREFBUF | Partly: the mode table is still an Inference |
| D-R19-04 / R18-MCU-01 / -03 gate networks | Confirmed |
| D-GAP-05 IWDG window | Confirmed |

## Fix now (none changes the board)

- **R23-MCU-01.** Add a "Bring-up configuration" bullet to M3_R10 "Firmware" and to the binding obligations. It covers:
  - option-byte programming and readback;
  - the LDO supply and the VOS for 200 MHz;
  - HSE, PLL and CSS;
  - the USB VBUS-sense override.
- **R23-MCU-02.** Add the three exact single-open tap entries (BOOT0, VCAP1, VCAP2) and list them as respin items (a second via, or R5 on F.Cu).
- **R23-MCU-03.** Correct round22_alternates.md §2.3, its summary row and its docs note, and add the ST ISM driver 256 g enum caution.
- **R23-MCU-04.** Change TT_a to TT_u in binding obligation 29.

## Coverage limits

- RM0433 and AN2606 downloads timed out (st.com), so the statements that depend on RM0433 remain Inferences.
- No firmware exists and no hardware was measured.
- DRC / ERC and single_via_opens were not re-run.
