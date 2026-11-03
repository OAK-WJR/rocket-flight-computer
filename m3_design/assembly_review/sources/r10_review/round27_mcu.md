# R10 round 27: MCU lens (Claude)

- Target commit `816038c`; board SHA-256 `a0ec075e…` before and after (unchanged).
- Totals (real errors only): **0 Critical / 0 Major / 1 Minor**.

## Findings

### R27-MCU-01 (Minor, doc): the binding note claims every DS12110 citation is Rev 8, but cites Rev 11 Table 109

- **Statement:** `r10_binding_note.json` `sources.mcu_revision` (generated from `m3_design/r10_sch_check.py`
  lines 242–243) says "every DS12110 citation in this note is Rev 8 (April 2021), revision V electrical chapter …".
- **Contradiction:** the same note's R5-MCU-04 obligation (`firmware_obligations[29]`, from r10_sch_check.py line 307)
  says "the 4.0 V ADC-mode maximum and the 6.0 V FT cap were read from Rev 11 Table 109 in round 14 and are kept as
  design limits (Inference: not in Rev 8, Rev 11 not re-read)". `docs/M3_R10.md` "Sources and datasheet revisions"
  itself lists these two limits as labelled Rev 11 exceptions; the note's sentence has no such carve-out.
- **Not considered before:** R23-DOCS_BINDING-04 covered AGENTS, ORDERING and parts_qualification. No round 23–26
  triage mentions "Rev 11", "Table 109" or this sentence.
- **Impact:** low. A reader trusting the sources line would look up Table 109 in Rev 8, where it is a different table.
- **Fix (generator text only; the board is unchanged):** append "except the two design limits labelled as read from
  Rev 11 Table 109 in round 14 (the 6.0 V FT cap and the 4.0 V ADC-mode maximum; R5-MCU-04, Inference)". Regenerate
  the note and optionally pin the words in `test_r23_binding_note_rules_and_pin_table`.

## Fix verification

| Change | Measurement | Verdict |
|---|---|---|
| D-R26-03 chatter obligation | Independent worst-corner EN model (SLVSFC9C p. 9): 8.066 ms single drop-out at 5.713 V; 10.345 / 20.111 / 26.023 ms at 6.0 / 7.4 / 8.4 V; 6.300 ms at 5.5 V. Late block: 7.501 ms at 5.713 V, 7.629 ms at 5.73 V, 5.871 ms at 5.5 V, 9.594 ms at 6.0 V. EN at the 7 ms line: 1.1295 / 1.1330 V. The line holds to 5.6465 V. Trip fractions: 19.7 / 19.6 / 14.8 / 4.5 % at 5.713 V and 24.4 / 24.3 / 8.3 % at 6.0 V. Exchange identity checked algebraically. Turn-on 30.3–130.3 ms | confirmed |
| D-R26-03 rule 8 | Four-stall points: 5.7132 V healthy at 1.2787 A; 5.5576 / 5.5555 V with the match shorted; 5.5084 V with match and leads shorted. U9 turn-off 4.802 V (4.778 V without D402). Hold-up 0.103–0.164 ms with all ports on, 0.291–0.430 ms shed (ratios 0.22–0.31) | confirmed |
| D-R26-02 / -04 (PE4 network) | pcbnew shape distance on all layers with fills. 3V3 to PYRO1_GATE 1.0588 mm; 3V3 to PYRO1_GATE_N 1.0652 mm; 3V3A to PYRO1_GATE 1.1455 mm; PYRO1_OUT to 3V3A 1.0400 mm | confirmed |
| D-R26-01 (AUX UART) | Both GND vias exist. The PC6 / PC7 map through R471 / R470 to J440.3 / .4 is unchanged | confirmed (MCU side) |

## Main checks (all clean apart from R27-MCU-01)

- **Pin maps agree on all 100 U1 pins:** the board pads, `schematic.net.xml`, `pin_table.tsv` and the binding note.
  The note's netlist, pin-table and circuit hashes match the files.
- **Against DS12110 Rev 8 (cached PDF):**
  - pin numbers and names;
  - alternate functions and ADC channels;
  - every Table 9 and Table 10–14 page citation in pin_table;
  - the cited Tables 119 / 120 / 122 / 126 / 127 / 128 / 146 / 147 / 157 / 159 / 160 / 189 / 192 and Table 9 note 7.
- **Every reset_contract part:** value and nets match the board.
- **Cited vias:** Q120 / Q121 gate barrels, R91 / U1.28 second vias and the EN via.
- **Interface pin facts:** J410 / J420 / J440 / J9 pin order, the microSD pins, MS5611 PS / CSB, and the TXU0202 pins.
- **U4:** the pin map and the axis map against DS14623 Figure 5.
- **IWDG arithmetic:** 28.571 / 32.653 / 34.853 ms.

## Observations (8, not counted)

The JSON lists all eight. In short:

- the pin-map agreement;
- the DS page citations;
- the AF, ADC and wake-up mapping;
- the reset_contract parts;
- rule 4's "0.93–1.01×", a conservative envelope of the round 23 case table rather than of the two quoted currents;
- the 25 MHz HSE harmonic at 1575.0 MHz (no GNSS on the board; Inference);
- PC14's 3.3 mA edge current, already recorded;
- the PA6 lower edge with 1 % parts, still above U9's corner in BAT_IN terms.

## Coverage limits

- AN2606, RM0433, DS15034 and DS12110 Rev 11 were not read.
- The power-lens figures were not re-derived.
- Other lenses' round 27 reports were not opened.
