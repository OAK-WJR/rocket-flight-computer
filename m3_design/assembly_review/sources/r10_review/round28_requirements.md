# R10 round 28: requirements lens (Claude)

Target commit `19dd0b5`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (the same before and after).
Totals: **0 Critical / 0 Major / 2 Minor** (real errors only).

## Findings

- **R28-REQUIREMENTS-01 (calc, Minor): F4's hinge-moment range for flight 2 is wrong at its lower end.**
  - F4 says "the derived max-q hinge moment at large deflection is 73–84 % of the HV6120 stall torque", as a flight-2 figure.
  - Running the source script (R23 `hinge.py`) again gives:
    - 73 % for the **K850DM** high-q case (M1.65, 172 kPa, 0.386 N·m);
    - 77 % (M1.82, 212 kPa) and 84 % (M2.13, 286 kPa) for the L1000W cases.
  - R23-REQUIREMENTS-05's own "measured" field gives L1000W as 0.41–0.45 N·m, which is 77–84 %.
  - Over all 18 L1000W cases of the derived envelope (same method, tab 8 × 26.5 mm from VEHICLE.md), the range is **63.9–84.3 %**:
    - low end: M1.59, 142 kPa, 0.338 N·m;
    - high end: M2.13, 286 kPa, 0.447 N·m.
    - Probe: `.supervisor/r28_requirements/hinge_all.py`, `hinge_l1000w.txt`.
  - Fix: change F4 to "about 64–84 % over the derived envelope (77–84 % nominal to high; linear theory, Inference)".
  - The conclusion is unchanged, and there is no board impact.
- **R28-REQUIREMENTS-02 (doc, Minor): line 36 cites a 525 s figure the Temperature row no longer has.**
  - REQUIREMENTS line 36 asks to re-check "the Temperature row's 525 s".
  - The Temperature row (line 93) says "about 1200 s". Round 23 (`9b27268`) changed it from 525 s and left line 36 as it was.
  - Fix: drop that clause, or point it at the 1200 s now in the row.

## Fix verification

- **D-R27-03: confirmed.**
  - The port symbol pins are 4V8 / GND / TXO / RXI, and J410, J420 and J440 use it.
  - The netlist pin functions are 4V8_1 … RXI_4. J9 keeps the camera names.
- **D-R27-01: confirmed.** Recomputed four-stall pack sag: 5.8810 V from 7.4 V and 4.3887 V from 6 V. The fire budget's 5.713 V is unchanged.
- **D-R27-02: confirmed.** The binding-note sentence names the two Rev 11 limits.
- **D-R26-03 (F4 / F6 text): partly.** The text consistently quotes 5.71 V, 7.50 ms and 8.07 ms. The EN model was not re-run.

## Observations (not counted, 16)

These are in the JSON. They cover:
- F10 / J9 pin-to-MCU tracing, all correct;
- the schematic symbols and the silk legend positions;
- the converter feedback, PA6 divider, bleed and sense-bank values;
- the EXTI pins;
- the mounting holes and outline;
- the fire-path widths;
- the VEHICLE-derived stack, sled, wire-room and ISA numbers, all re-derived and correct;
- the F6 hold-up arithmetic;
- the M1 / M3 figures against the fab files;
- the disclosed F1 35 s ΔT recompute;
- P3's 28–37 g, already observed in round 27.

## Coverage limits

- No check.sh, DRC or route_check run.
- The EN, hot-plug, fire and thermal models were not re-run.
- The envelope was not re-simulated.
- Datasheets were not re-read.
- Supplier data was not re-queried.
