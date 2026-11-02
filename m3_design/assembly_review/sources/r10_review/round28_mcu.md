# Round 28 — MCU lens (Claude)

- Target commit `19dd0b52482c6cb2648de206715ab02a9a4b5394`; board SHA-256 before and after
  `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (unchanged).
- Totals: **0 Critical / 0 Major / 2 Minor** (real errors only).

## Findings

| ID | Kind | Severity | Finding |
|---|---|---|---|
| R28-MCU-01 | doc | Minor | The first-article check "meter U3.3 (QSPI_IO2) to R127.1 (the PE4 gate network): it must read open" is wrong for an intact board. It appears in ORDERING.md:651, M3_R10.md:1088–1089, FMEA_REDUNDANCY.md:38 and the binding note's rule 3 (r10_sch_check.py:366). |
| R28-MCU-02 | doc | Minor | parts_qualification.md:914 says "PB1 is a TT_a pin", but DS12110 Rev 8 Table 9 p. 70 gives TT_u. R10_VALIDATION.md:1915 says "docs already say TT_u", which is also false. |

### R28-MCU-01
- **What is wrong.** On `a0ec075e…`, R127.1 (PYRO1_GATE_N) has a DC path to GND of 910.9 Ω (R127 1 kΩ in parallel with R126 220 Ω + R128 10 kΩ). QSPI_IO2 is only U1.1 and U3.3, and both pins have input clamps to GND. DS12110 Rev 8 Table 120 p. 213 allows −5 mA injection on FT pins, and its note 4 says negative injection happens when VIN < VSS.
  - With the meter's positive lead on R127.1, a diode test therefore reads about 0.6 V + 0.91 V ≈ 1.5 V (not OL). Ohms mode reads a finite kΩ value on any meter whose test voltage is above a junction drop.
  - With the leads reversed, it reads open.
  - So a good board fails "must read open" in one polarity on common meters. The result depends on the meter and on the polarity.
- **What it contradicts.** The procedure's own source, round23_safety_severity_check.md lines 212–213: "Require no beep and > 100 Ω … a diode-plus-1 kΩ path or open if intact".
- **Fix.** In all four places, use the source's criterion: no beep and > 100 Ω in both polarities. Say what an intact board reads (open one way, a diode drop plus 0.91 kΩ the other) and what a bridge reads (near 0 Ω). Then regenerate the binding note.

### R28-MCU-02
- **What is wrong.** R23-MCU-04 corrected "TT_a" to "TT_u" for PB1, but only in the binding note. The same false phrase is still in the parts record. The 4.0 V limit is unchanged (Table 119 gives 4.0 V for every TT_xx pin), so only the pin-type fact is wrong.
- **Fix.**
  - parts_qualification.md:914: change "TT_a pin" to "TT_u pin (DS12110 Rev 8 Table 9 p. 70)".
  - R10_VALIDATION.md:1915: correct the "docs already say TT_u" note.

## Fix verification

| Item | Verdict | Evidence |
|---|---|---|
| D-R27-02 (binding note's Rev 8 / Rev 11 sentence) | Confirmed | The only non-Rev 8 DS12110 citation in the note is the R5-MCU-04 Rev 11 Table 109 pair that the sentence names. Every other table and page cited resolves to Rev 8. The unit test passes, native K-binding regeneration matches, and the note SHA is `e8f10fb3…`. |
| D-R27-03 (port symbol, U1 UART side) | Confirmed | J410 / J420 / J440 pins read 4V8 / GND / TXO / RXI. TXO reaches PD8 / PB13 / PC6 and RXI reaches PD9 / PB12 / PC7 through the 1 kΩ resistors. |
| D-R26-04 (3V3 / 3V3A to PE4's gate nets) | Confirmed | Minimum spacing is 1.059 mm on F.Cu (R128.1 to the 3V3 via at (19.55, 55.825)). |

## What was checked (all consistent)

**Pin map**
- U1's 100 pads, the fresh schematic netlist, the binding note's u1_pins and pin_table.tsv agree (0 mismatches). The netlist pin names match the pin_table port column.
- Every pin number matches DS12110 Rev 8 Table 9 (LQFP100).
- Every Table 9 and Table 10–14 page cited in pin_table holds the cited row.

**Datasheet facts**
- AF numbers are correct, including the trace pins (PC1 is TRACED0, PE4 TRACED1, PE2 TRACECLK).
- Pin I/O types are correct where cited.
- ADC channels are correct.
- Every DS12110 table and page cited in the binding note was checked against the Rev 8 text.

**Copper and calculations**
- The resistor and capacitor values the firmware obligations rely on match the board, as do the second-via coordinates.
- These calculations were re-run and are correct: the IWDG timing, the gate voltages against an internal pull-up, the VBUS_SENSE threshold and the loader drive currents.

**Hashes and checks**
- The board, netlist, pin_table and circuit hashes in the binding note match the files.
- K-binding passes.

There are 14 observations, none counted; see the JSON. Coverage limits: AN2606, RM0433 and DS12110 Rev 11 were not available or not re-read, and no gate seeds were run (the U1 map is enforced by contract() and K-binding).
