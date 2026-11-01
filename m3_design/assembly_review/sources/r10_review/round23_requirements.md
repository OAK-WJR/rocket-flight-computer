# Round 23 - requirements traced to the flight's physics (Claude)

Target commit c70d261; board SHA-256 `5516eeec…` before and after (also identical in `git show` of ec8cb98 and c70d261).

**Totals: 0 Critical / 0 Major / 8 Minor** (7 new, 1 carried from R21-REQ-05). All eight are text-only. The board meets every derived number. The gaps are in how the requirements are rooted in the flight, and in what they cover.

## Derived envelope (Inference)

Method: a 1-D vertical model (`.supervisor/r23_requirements/flight1d.py`, 54 cases). Inputs:
- thrustcurve.org samples for the K850DM (1869 N·s, 2.0 s, 1094 N max, 2041 g / 1224 g) and the HP-L1000W (2714 N·s, 2.7 s, 1261 N max, 2194 g / 1400 g);
- dry mass 1.6, 2.1 or 2.7 kg;
- a generic Cd(M) curve scaled ×0.8, ×1.0 or ×1.3;
- sites at 0 m and 1200 m, ISA atmosphere.

| | K850DM | L1000W |
|---|---|---|
| Peak specific force | 25.5–34.6 g | 27.7–36.6 g |
| Burnout drag deceleration | 3.6–12.2 g | 4.9–14.5 g |
| Max Mach / q | 1.17–1.65 / 84–172 kPa | 1.54–2.20 / 142–286 kPa |
| Apogee AGL / time | 3.5–5.3 km / 23–29 s | 4.8–7.6 km / 26–34 s |
| Apogee pressure / ambient | 440–656 hPa / −8…−27 °C | 317–556 hPa / −16…−42 °C |
| Descent, 36 in chute (Cd 1.5 / 2.2) | 424–848 s | 565–1149 s |
| Landing speed | 5.2–8.0 m/s | 5.1–8.0 m/s |
| Whole flight | 449–877 s | 592–1183 s |

## Findings

- **R23-REQUIREMENTS-01 (Minor, carried R21-REQ-05): the envelope is still undefined.**
  - The table cell still carries the 21.5 km drag-free bound and 460–525 s.
  - The Temperature row says "flight 2 lasts up to 525 s", against about 1180 s derived.
  - F5 says "about 2 MB"; the derived worst case is about 3.5 MB, which the 16 MB QSPI still holds.
  - Fix (text): put in the table above, labelled Inference.
- **R23-REQUIREMENTS-02 (Minor): the ≤ 30 s control window has no physics root.**
  - Time to apogee is up to 34 s.
  - Over 34 s, F1's allowed bay change drops from about 9 °C to about 8 °C.
  - Fix (text): tie the window to a stop condition (a q floor or apogee), or call 30 s a design choice.
- **R23-REQUIREMENTS-03 (Minor): F3's "≥ 10 km" comes from the ADC range, not the accuracy band.**
  - The MS5611 error band (±2.5 mbar) covers only 450–1100 mbar (datasheet p.2).
  - Flight 2's derived apogee is at 317–556 hPa, so apogee is detected where the maker gives no accuracy figure.
  - Fix (text): restate F3 as readings to ≥ 300 hPa, and add a cold vacuum-chamber characterisation.
- **R23-REQUIREMENTS-04 (Minor): P3's 100 g landing basis assumes 6 m/s.**
  - A 36 in flat chute gives 6.2–8.0 m/s, which is 98–163 g at the same 20 mm crush.
  - The owner's "200 g" option is then only 1.2× over that, not 2×.
  - Fix (text): set the load from the chosen chute; state the option as 2 × that landing load.
- **R23-REQUIREMENTS-05 (Minor): servo stall can be a normal operating case on flight 2, not only a fault.**
  - At flight 2's max q, a 15° deflection gives a hinge moment of 0.41–0.45 N·m, 73–84 % of the HV6120's 0.53 N·m stall torque (linear theory, `hinge.py`).
  - So the four-stall sag (5.73 V, which gives only 8.5 ms of chatter immunity) can coincide with boost vibration on J400.
  - Fix (text): a q-scheduled deflection limit, a pack that holds ≥ 5.92 V under four stalls, or the chatter bench test run at 5.73 V.
- **R23-REQUIREMENTS-06 (Minor): nothing covers the time after landing.**
  - Nothing in REQUIREMENTS says what the board does from touchdown to recovery.
  - Derived drift is 2–11 km, so the vehicle must be found by its GPS and radio.
  - Q_recovery has no duration.
  - F6 services the watchdog only "through landing", but an IWDG cannot be stopped.
  - FMEA F-8 says "GNSS turns off" after landing, which R10's always-on ports cannot do.
  - Fix (text): add an F12 "Landed" row:
    - PC1 and PE4 low and latched;
    - IWDG serviced until power-off;
    - GPS and radio beacon kept on;
    - a search time T_rec that sets Q_recovery.
- **R23-REQUIREMENTS-07 (Minor): no board check on the pack during a long pad hold.**
  - "≥ 7.4 V resting at launch" is only an operating assumption.
  - PA6 VLOGIC_SENSE already reads the pack, but no requirement asks firmware to telemeter it or to refuse READY on a low pack.
  - Fix (text): add that requirement to F7 / F11.
- **R23-REQUIREMENTS-08 (Minor): no in-flight thermal basis.**
  - At Mach 1.9 the recovery temperature at the wall is about 200 °C. The 1.6 mm wall's diffusion time is about 8 s, which is inside the 30 s window.
  - Ambient falls by 23–35 °C during the ascent.
  - The descent spends 7–19 min in air down to −42 °C, against the −20 °C site floor. LS120 and J430 are rated only to −20 °C.
  - Fix (text): log the bay temperature on flight 1, and make IMU temperature compensation an F1 requirement.

Compared with round 22: its requirements report (R22-REQUIREMENTS-01 to -04) had none of these. All eight are independent.

## Flight-phase coverage

| Phase | Covered by | Gap |
|---|---|---|
| Storage and transport | Storage row | — |
| Bench / harness work | F8, F9, ORDERING 8.3 | — |
| Rail arming, pad hold up to 2 h | Pad arming, Pad time, Temperature (70 °C) | Pack-voltage go / no-go (-07) |
| Launch detection | F8, AGENTS §2 | — |
| Burn, 2.0–3.0 s | F1, F2, F4, F6 | Stall during boost on flight 2 (-05) |
| Transonic and coast | F3 (baro not trusted near Mach 1) | Window length (-02), thermal (-08) |
| Apogee and deployment | F7, F3 | Baro accuracy at the apogee pressure (-03) |
| Descent, 7–19 min | F5 (≤ 50 Hz log) | Cold (-08) |
| Landing | P3 | Basis (-04) |
| Post-landing to recovery | F11 (annunciation only) | -06 |

## Fix verification

| Change | Verdict | Measured |
|---|---|---|
| D-R22 pass, whole | Confirmed | Board hash unchanged. The Gerber zip differs only in KiCad date lines (14/14 files identical without them). check_r10's removed lines are refactors: the PTH-inner, DRU and ILIM / GND single-open checks are still present. |
| D-R22-04 (row 30 reason, EN 2.03 / 2.06 V) | Confirmed | 227 kΩ × 220 nF = 50 ms; 6.8 µA; 2.032 / 2.063 V; the spots are 0.671 mm from the three vias |
| D-R22-03 | Confirmed | 5.456 / 11 = 0.496 V; 9.77 / 11 = 0.89 V; the old text is gone |
| R22-REQUIREMENTS-03 / -04 text | Confirmed | ESD handling in F8 / F9 and ORDERING 8.3; C88 in the OQ-6 bullet; 23:23Z cited |
| D-R21-03 | Confirmed | The three schematic notes read as recorded |
| R21-REQ-03 | Confirmed | J440 is in the Camera row |
| R21-REQ-05 | Partly | Still flagged, not replaced (-01) |

## Fix now

All eight are text-only (REQUIREMENTS, ORDERING 8.1.1, FMEA F-8 note); none changes the board. Priority: -06 (Landed row), -01 (envelope), then -03 and -05.

## Closed candidates

- ±64 g: rooted, 1.75× over the derived 36.6 g.
- Low-g range: burnout deceleration ≤ 14.5 g is inside ±16 g, a thin margin.
- ±4000 dps: one tab stuck at 15° gives about 1000 dps at M0.9 (the historical figure) and 1440–2160 dps at M1.9; about 1.8× margin.
- U4 lever arm: 3 g centripetal at 4000 dps.
- Log volume: fits.
- Baro range: 8.8 km MSL is under 10 km.
- Tripoli rules: 11-6 is met by CH1 plus the Blue Jay; landing at ≤ 8 m/s is under 11-1's 10.7 m/s.
- GPS 500 m/s limit: consistent with tracking-only use.
- Recorded or owner items, not re-filed: pad-energy oversizing, hold-up, P3 factor, cost, tabs, row 18, stock, J400 ESD.

## Coverage limits

- The trajectory is a 1-D model with a generic Cd. It brackets the flight; it does not predict it.
- The roll, hinge and thermal figures are linear-theory or order-of-magnitude Inferences.
- No KiCad, DRC or check.sh run.
- AeroTech pages returned HTTP 429, so the motor data come from thrustcurve.org.
- Probe files are in `.supervisor/r23_requirements/`.
