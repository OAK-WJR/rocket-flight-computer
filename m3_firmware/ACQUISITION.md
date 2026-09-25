# v0.2 bench acquisition: implementation rationale

This firmware is for bench diagnostics of the ordinary power / acquisition board; it contains no flight-state estimation, attitude control or actuation. It never touched a real board. A successful sample read, a formula matching the maker's example and a passing DRC are three different kinds of evidence, and none of them certifies whole-board reliability.

## ADC and the native netlist

| Item | Connection / configuration | Basis |
|---|---|---|
| VLOGIC_SENSE | PC2_C, LQFP100 pin 17, ADC3_INP0 | ST DS12110 Rev 11 Table 9 p. 67 |
| V3V3_SENSE | PC3_C, pin 18, ADC3_INP1 | Same table |
| Dividers | R60/R61 = 100k/10k; R62/R63 = 10k/10k | Every build checks the values and both end nets from the native XML, scaling by 11 and 2 |
| Pin isolation | GPIOC2/3 analog, no pulls; PC2SO/PC3SO set to 1 | ST HAL's OPEN definition / implementation; disconnects the internal link between ordinary PCx and the dedicated PCx_C |
| Clock | HSI64 → CLKP → ADC asynchronous ÷16 | ST's polling example for the matching version; no PLL; the H743 rev V has an extra fixed ÷2, giving a 2 MHz analog ADC clock (4 MHz on rev Y) |
| Acquisition | 16-bit, single software trigger, DR polling, overrun preserved, no DMA | Matching HAL; per channel: configure, wait, start, poll with a 20 ms limit, read, stop |
| Sampling time | 810.5 cycles; an extra 1 ms wait after configuration | ≥ 202.6 µs sampling at the 4 MHz maximum; DS12110 VREFINT minimum sampling 4.3 µs, LL recommends 5 µs for internal reference settling |
| Calibration | Single-ended offset + linearity calibration after init, 200 ms limit, once per boot | Uses the same version's LL start operation; the HAL's own widest timeout of 633600000 loops is unsuitable for this bench configuration. The HAL's conservative 165010 cycles is 82.5 ms at 2 MHz |

If ADC calibration fails it is not retried in a way that stalls the main loop; the error is recorded and diagnostic heartbeats continue. Private data / valid bits are cleared on every sample, so a failed channel has no path to "reuse the last reading". SRAM is published only after a whole cycle ends, so the previous complete cycle can still be read during acquisition; a result that stops updating is caught by the host's heartbeat / sample-sequence checks.

### The H743 reference-calibration version trap

In the pinned HAL v1.11.6, `__LL_ADC_CALC_VREFANALOG_VOLTAGE` rescales the observation to 12 bits while its comment still says 16 bits. For the H743, v1.11.4's implementation and comment both use 16 bits, and the current release notes record the change to 12 bits. This difference was found by checking the specific part; the calibration format of the H723 and others must not be applied to the H743.

This firmware explicitly uses, for the H743: `VREF+_mV = round(3300 × VREFINT_CAL16 / ADC_REF16)`, and does not call the ambiguous generic conversion macro. Raw calibration / reference codes are kept; conversion is refused if the calibration value is outside 20000–30000 or the derived reference is outside 1.8–3.6 V, with no guessing between 12 and 16 bits. That range is only a loose plausibility gate and does not prove calibration accuracy. External dividers use 64-bit intermediates to avoid overflow when multiplying by 11.

Sources: [current H743 datasheet](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf), [matching ADC polling example](https://github.com/STMicroelectronics/STM32CubeH7/tree/5abb9764b32e11a6557b90bf39531528019b5761/Projects/NUCLEO-H743ZI/Examples/ADC/ADC_RegularConversion_Polling), [current LL file](https://github.com/STMicroelectronics/stm32h7xx-hal-driver/blob/a1996eed9172b59887bafaaa0ea1816ea14d48b5/Inc/stm32h7xx_ll_adc.h), [v1.11.4 for comparison](https://github.com/STMicroelectronics/stm32h7xx-hal-driver/blob/v1.11.4/Inc/stm32h7xx_ll_adc.h). The pinned commit / blob / SHA of every current driver file is in `vendor_manifest.json`.

## Pressure / temperature acquisition

First verify the power-up PROM CRC and non-empty coefficients, then send the D1 OSR4096 command 0x48 and the D2 command 0x58 to address 0x77. After each conversion's STOP, wait 11 ms (more than the maker's 9.04 ms maximum), then send the 0x00 read command, STOP, the read address and three data bytes, with the last byte NACKed. Each SCL wait has a 5 ms limit; no bus scanning, no endless retries.

Each cycle keeps D1, D2, their separate completion times and valid bits. A reading of 0 or 0xFFFFFF is never a valid pressure; partially successful records keep the raw bytes already read. Conversion uses TE B3 pp. 8–9 second-order temperature compensation, covering the below-20 °C and below-−15 °C branches; the C arithmetic explicitly uses 64 bits and truncation toward zero. The host compares against an independent 32-significant-digit decimal implementation, allowing ≤ 3 Pa / ≤ 0.02 °C of difference from integer steps. The maker's room-temperature example is D1 = 9085466, D2 = 8569150 → 100009 Pa, 20.07 °C.

The completion time is not the exact conversion-trigger edge, and D1/D2 are not measured simultaneously. The slow GPIO bus is only suitable for bench checks: a nominal acquisition period of at least 1 s, with no catching up on missed periods. A run of plausible readings still cannot exclude an internally frozen sensor, a blocked port, or real accuracy / noise problems; those need physical stimulus and independent instruments.

Source: [TE MS5611-01BA03 B3](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Data+Sheet%7FMS5611-01BA03%7FB3%7Fpdf%7FEnglish%7FENG_DS_MS5611-01BA03_B3.pdf%7FCAT-BLPS0036) (2017 edition cached, not claimed to be the latest).

## Records and judgement

Protocol version 2 occupies 512 bytes at the fixed address 0x24000000: the first 52 words keep identity / boot diagnostics, words 52–81 hold acquisition data, 82–126 are reserved as 0, and word 127 is a CRC32. The 16-byte header is read first to check version / length before the extension area; an old v0.1 is never treated as v0.2. The protocol change touched the linker script, the transport whitelist, the decoder and the fault tests together, without adding any target-memory write permission.

`--samples 2..30 --interval 1.2..10` bounds host acquisition, and the worker process has an overall timeout. Raw transactions / failed attempts stay in the JSON, decoded samples go to JSONL. A fault in any valid record is never removed from the summary by a later recovery. JSONL marks its source explicitly: software tests are fixed as `SYNTHETIC_FIXTURE` and must never be used as hardware records.

`ADC_MEASUREMENTS/BARO_MEASUREMENTS = PASS` only proves raw values were read, conversions are consistent and the corresponding records are live; 3V3 ± 5 % and VLOGIC 3.5–8.6 V are screening windows. Whole-board status stays INCOMPLETE or ISSUES_FOUND. USB, flash quad read/write / power-loss logging, IMU samples, camera UART, watchdog and environmental stress had no passing evidence in this round.
