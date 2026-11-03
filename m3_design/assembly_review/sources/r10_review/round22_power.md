# Round 22 power review (Claude)

Target commit `ec8cb98`. PCB SHA-256 `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1` before and after (canonical file and the git-archive probe copy).
**Result: 0 Critical / 0 Major / 2 Minor (both new).** Evidence: [round22_power.json](round22_power.json); probe files in `.supervisor/r22_power/`.

Scope: battery entry to every rail. First the round 21 changes: the U2.1 second path, the named single-point taps, the 0.55 mm inner PTH refill, and R81 / C87 at U9. Then U9, R166, C88 / C84, VLOGIC, 3V3 / 3V3A, PORT_5V3, PORT_4V8, U402, RAW_ACT and the R134 fire path.

## Findings

**R22-POWER-01 (Minor): the GND vias that SINGLE_OPEN_EXCEPTIONS allows as TPS2553 ILIM legs are each U10's and U402's only ground.**
- U402.2 B(30.70,59.00) sits in a 5.7 mm² B.Cu GND island whose only via is (32.30,59.50).
- U10.2 B(11.30,27.50), with R7.2 (CC1 Rd), sits in a 2.9 mm² island whose only via is (9.00,27.837).
- Seeded DRC opens each one: 1 unconnected.
- The exceptions R85.2 / R430.2 give the reason "open ILIM leg, lower limit, fail-safe". But the open removes the IC ground itself. TI states no open-GND behaviour (SLVS841G p4, p25), so the consequence is an Inference. It is camera or bench-USB loss, possibly with injection into an MCU pin; there is no flight-safety effect.
- R8.2 (CC2 Rd) is another single-via island, at (9.95,30.60).
- Fix now (text and check only): reword both reasons, add GND taps for U10.2 and U402.2 with exact exceptions, and list them in the retained deviations. At the next board change, add a second GND via to each island.

**R22-POWER-02 (Minor): PA6's VLOGIC sense tap hangs on one via.**
- R60.1 (100 k to PA6) reaches VLOGIC only through (34.50,63.00). Seeded DRC: 1 unconnected. Open, PA6 = 0 V through R61.
- Under the documented firmware rule, the analog-watchdog shed would then stop QSPI / SD writes and UARTs and park the port TX pins for the rest of the flight (Inference; no pyro or deployment effect).
- PA4 (LOGIC_SOURCE_ST) has the same issue: it reaches U11.9 / R91 through one via, (30.85,51.80), and R91 reaches 3V3 through one via, (28.10,60.00).
- None of these taps is in SINGLE_OPEN_TAPS.
- Fix now (text only):
  - a PA6 plausibility rule: VLOGIC cannot be below the AP63203's 3.8 V minimum while 3V3 regulates, so PA6 below about 0.25 V, or a trip with the MCU still running, is a sense fault: log it and resume;
  - a PA4 consistency rule;
  - PA6 / PA4 readings added to the ORDERING 8.3 pack-power checks.
- At the next board change: second vias for these taps, and survey entries for them.

## Fix verification

| Decision | Verdict | Measured |
|---|---|---|
| D-R21-01 | confirmed | All 31 plated pads ≥ 0.550 mm to inner foreign copper (own survey). JLC 0.3 mm re-read live. Inner power fills are one piece each. RAW_PROTECTED U9→U400 37.77 mΩ (unchanged); neck 1.05 mm B.Cu at U9; median In2 cut 1.40 mm; no neck at J1. 3V3 L1→U1 7.31 mΩ; L1→SD 10.22 mΩ; no neck at J3. The J1 / J400 strips are cross-links between wide lanes; the J3 strips feed no load. IPC upper bound with all the current in one strip ≤ 6 °C. Not marginal. |
| D-R21-02 | partly | Every 3V3 via seeded open in turn (31): U2.1 is never cut. With both U2.1 vias open, U2.1 is cut (the control works). The exception seeds reproduce. The U401.3, R87.1, R85.1 and R81.1 / C87.1 reasons are correct (Inferences as labelled). The R85.2 / R430.2 reasons are incomplete (R22-POWER-01). |
| D-R21-03 | confirmed | The battery_entry note matches the board: Q120 is fed from J1.1 by the B.Cu trunk, C88 is at U9, U9 is TPS259470L. |
| D-R21-04 | confirmed | Hop and run as recorded. BAT_ENABLE's nearest live copper is unchanged (BAT_IN 0.200 mm, U9 pin pitch). |
| D-R21-05 | confirmed | Positions as recorded; 3.889 / 2.013 mm with one via (an open floats EN; recorded respin item). The R81.2 / C87.2 GND piece has 2 vias, robust to any single open. Independent timing: 30.3–128.6 ms on; worst immunity 10.65 / 20.47 / 26.41 ms; 8.50 ms at 5.73 V; 10 ms needs 5.917 V. EN ≤ 2.06 V. 940 kΩ ≥ TI's 350 kΩ for reverse polarity. |
| D-R20-11 | confirmed | Reproduced. |
| D-R19-09 / D-R20-02 | confirmed | 20 doubled power-feed vias each seeded open: 0 unconnected. U11.2 is the carried single via. |

## Fix now
- R22-POWER-01: exception text, two GND taps and a deviation-list entry (no board change).
- R22-POWER-02: firmware plausibility rules for PA6 and PA4, and ORDERING 8.3 checks (no board change).

## Closed without a finding
- The BAT_IN 1.0 / 0.5 mm via (17.5,87.3) carries 2.9 A: recorded, held by K-power, fail-safe.
- The R92 bleed's single via: loads discharge RAW_PROTECTED to U400's UVLO (about 3.06 V, DS41326 p5), so TI's −15 V floor governs (Inference).
- R89's pull-up via predates round 21.
- J1.2 relief: 12 × 0.3 mm spokes.
- U9 ILM gives 3.96–4.84 A.
- The fire path is unchanged; a shorted match warms the IGN copper by about 10 °C adiabatic.
- Local capacitor and sense single vias leave the main output capacitors in place.
- BAT_ENABLE has no new approach to any live net.

## Limits
- No thermal sim.
- Seeds keep the existing fills (barrel-crack model).
- Hot-plug and hold-up models not rerun.
- The GND fire-return window solve had not finished when this was written.
- Open-pin behaviours are Inference.
- No legal-spot scans for the proposed vias.
- Tab bands not re-measured.
