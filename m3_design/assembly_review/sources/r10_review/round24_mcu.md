# R10 round 24: MCU lens (Claude)

Target commit `f2b8251`. Board SHA-256 `1407e8506efbac0f664b3aeb65568c32ae9670c9b45b502a465cba1130de522e` before and
after the review. Machine-readable copy: `round24_mcu.json`.

**Totals: 0 Critical / 0 Major / 4 Minor.** All four are false documents (kind doc). No copper, pin-map or gate error
was found.

## Findings

| ID | Kind | Severity | What is false | Evidence on 1407e850 | Fix |
|---|---|---|---|---|---|
| R24-MCU-01 | doc | Minor | M3_R10 Firmware rule 5 (lines 965-967) and binding-note obligation 40 (from `r10_sch_check.py` line 319): "R91.1 and U1.28 each hang on one via (D-R22-02)" | D-R24-08's vias LOGIC_SOURCE_ST (30.45,51.4) and 3V3 (28.1,59.4) exist. `single_via_opens` gives no single point for either tap. FMEA line 41 already says they have a second via | Re-word rule 5 in both sources, then regenerate the binding note |
| R24-MCU-02 | doc | Minor | M3_R10 rule 4 (lines 963-964): "Respin: a second via at Q120's gate (16.2,73.3)". Binding-note obligation 39: "Respin: a second via." R10_VALIDATION line 2250 (owner list §1): "Q120's gate via (16.2,73.3), the only link ... single via" | D-R24-02's barrel (15.4,72.85) is in place. Q120.4 has no single point. M3_R10 lines 348-351 and ORDERING line 650 already say this | Re-word rule 4 and the owner row to the two barrels, then regenerate the binding note |
| R24-MCU-03 | doc | Minor | R10_VALIDATION lines 2492-2493: BOOT0's maximum GND companion is "1.662077 mm" | The second BOOT0 via (14.2,46.0) is 2.000 mm from the nearest GND via, (14.2,48.0). The first via is 1.662 mm from its nearest GND via | Change the BOOT0 figure to 2.000 mm |
| R24-MCU-04 | doc | Minor | R10_VALIDATION lines 2402-2403: "QSPI lengths span 4.110955-14.524012 mm" | After D-R24-17, QSPI_IO2 is 14.102245 mm and QSPI_CLK is 7.428234 mm. 14.524012 mm was the 5516eeec figure | Change the span to 4.110955-14.102245 mm |

The rows in R10_VALIDATION §1, §5 and §6 cited above name no older board. Under the inventory-basis rule, they are
therefore statements about `1407e850…`.

## Fix verification

- **D-R24-03 (BOOT0): confirmed.**
  - Vias (13.8,45.6) and (14.2,46.0), joined on both F.Cu and B.Cu.
  - Clearances: F.Cu 0.150 mm to I2C1_SCL, B.Cu 0.211 mm to C31.1, hole edge 0.266 mm.
  - R5 stays on B.Cu, with R5.2 on the GND pour.
  - No single point. DRC 0.
- **D-R24-04 (VCAP2): confirmed.**
  - Vias (18.0,37.3) and (18.3,36.8).
  - Clearances: 0.211 mm to NRST, 0.328 mm to U1.72, hole edge 0.283 mm.
  - No single point.
  - VCAP1 stays single at (29.25,38.0), as its exact exception records.
- **D-R24-08 (U1.28 / R91.1): copper confirmed, records partly** (R24-MCU-01).
- **D-R24-02 (Q120 gate), as it bears on firmware rule 4: copper confirmed, records partly** (R24-MCU-02).
- **D-R24-17 on U1 nets: confirmed.** route_check reports 0 failing and `right_angle` 0.

## Checks run

- **U1 pin map:** all 100 U1 pads match `pin_table.tsv` and the binding note. Pins agree with DS12110 Rev 8 Figure 5,
  p. 55. The binding-note hashes match the files.
- **DRC:** kicad-cli DRC on a probe copy gives 0 errors and 0 unconnected.
- **route_check:** `--profile r10` gives 0 failing.
- **Single-open taps:** `check_r10.single_via_opens` was run for the BOOT0, VCAP, PA4, R91.1 and ACT_GATE taps.
- **Firmware rules against copper:**
  - PE4 and PC1 gate networks: 0.104 V and 0.218 V.
  - C126 / C128 roles, and U3.3 to R127.1.
  - PA4 / U11 ST polarity (TPS2121 IN1 is pin 7 USB, IN2 is pin 2 battery).
  - Divider scales: PA6, PB1 and PC0 / PC5 at 11 / 11 / 11.2, and PC8 at VBUS / 2.
  - MS5611 address 0x77, the pull-ups, VBAT and VREF+ ties, and the IWDG figures.
  - All consistent.
- **Seeded VCAP1 second via:** a via at (27.6,37.3) passes DRC after a refill. Joining it to the net fails
  route_check's detour (2.05×) and track_loop rules, so the VCAP1 keep decision stands.

## Observations (not counted)

1. In the `check_r10.py` comment above the U1.48 exception, BOOT0's second via is attributed to D-R24-05. It is
   D-R24-03.
2. D-R24-04's "no spot" wording covers only the B.Cu box east of C19. Spots exist to the west, but they fail
   route_check (see the seeded VCAP1 via above).
3. C19 and C20 nominally meet DS12110 Table 124, p. 216. Their operating capacitance and ESR stay owner row 10.
4. QSPI_IO2 is still 0.550 mm from U1.3. The B.Cu crossings of U4's body are unchanged.
5. SINGLE_OPEN_EXCEPTIONS has 11 entries, as documented.

## Coverage limits

- The DS12110 alternate-function tables were not re-parsed. `pin_table.tsv` is unchanged since round 23.
- The IMU axis map was not re-derived. U4 did not move.
- RM0433 was not read.
- No firmware, bench or physical tests were run.
