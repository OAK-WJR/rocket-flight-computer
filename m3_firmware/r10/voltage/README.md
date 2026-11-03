# R10 bench voltage acquisition core

This portable C module is a tested implementation step towards power diagnostics.
It is **not linked into the bench image**. There is no native ADC adapter yet,
and no ADC observations are available in the current ABI-v3 RAM record. No probe,
programming, load output or hardware test is involved in its tests.

The candidate adapter contract serializes five observations: ADC3 VREFINT before
the inputs, ADC1 PA6/VLOGIC, ADC1 PB1/camera, ADC3 VBAT, and VREFINT again.
`verify.py` checks the actual R10 MCU, both resistor dividers and 14 reference/input
endpoints against the native netlist. The old PC2_C/PC3_C driver does not bind here.

`voltage_core.c` advances once per poll through initialization, individual
conversions, a completed batch, or recovery. Initialization has a 500 ms bound,
each conversion 20 ms, and a batch 100 ms. A failed conversion keeps its earlier
raw observations and invalidates current results; the last complete sample,
timestamps, configuration and error history remain separately available.
Each read is confirmed on the following poll, so callback latency is included
in the deadline checks. Freshness starts at the conservative read-entry time,
not the later commit time.
Unsuccessful cancellation and a backwards timebase stop automatic retry.
Callbacks must themselves be bounded; a future adapter must prove that property.

Nominal conversion uses 10-bit samples and the 16-bit factory reference word:

```
reference_count = (reference_before + reference_after) / 2
VDDA_mV = 3300 * factory_cal_16 * 1023 / (65535 * reference_count)
input_mV = VDDA_mV * input_count * divider_ratio / 1023
```

The implementation retains this rational value until final rounding. External
divider ratios are both 11; internal VBAT uses 4. Zero external supply remains
a valid observation. Clipping, missing references, incompatible calibration or
configuration, and >2% bracketing-reference drift withhold converted results.
That drift line and the 1.8–3.6 V nominal reference screen are diagnostic policies,
not accuracy limits or proof that a rail is healthy. Maximum-code normalization
is the explicit conversion convention; ADC quantization/transfer error, reference
temperature drift, divider tolerance, settling and installed noise still need a
complete uncertainty budget. No electrical pass band is implemented here.

The [ST datasheet](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf)
(DS12110 Rev11, Tables9, 19/118 and 84/182) supplies the PA6/PB1 mapping, factory
3.3 V calibration and VBAT's nominal divide-by-four ratio with ±10% ratio error.
VBAT is tied to 3V3 on this board: its derived value is explicitly coarse and
cannot qualify a narrow 3V3 pass band. The pinned ST LL header documents 16-bit
reference observations; the generic helper's resolution normalization is not
copied here.

[ES0392 Rev16](https://www.st.com/resource/en/errata_sheet/es0392-stm32h742x743xig-st32h750xb-and-stm32h753xi-device-errata-stmicroelectronics.pdf)
Table2 provides the explicit revision allowlist. Sections2.9.7 and2.9.10 motivate
serial conversions and the conservative 10-bit configuration, including Y/W
above3.3 V. Recognizing an ID in this math module does not qualify its hardware.

Before integration: verify the complete applicable RM0433 initialization,
clock/regulator/calibration and channel-switch sequence, input settling, cleanup
and silicon-specific restrictions; implement/test the native adapter; version
the RAM protocol and preserve historical decode/address bounds. The official
manual's regulator/calibration/on-off sections were consulted, but direct full
PDF downloads failed. No complete initialization review is claimed.

Run the actual C state-machine fault cases under AddressSanitizer/UBSan and
compare nominal conversion against 2,000 independent rational-arithmetic vectors:

```
python3 -B m3_firmware/r10/voltage/test_voltage.py
```

The same tests are required by `tools/check.sh`. All inputs are scripted; passing
them establishes software behavior, not physical voltage acquisition or accuracy.
