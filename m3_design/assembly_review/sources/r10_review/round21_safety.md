# Round 21 safety review (Claude)

Target commit `accfff4947266a23cf60a63f3d92be047f5391b5`, PCB `0dc847761de94a45cf68b1c82ec91f38e9d4ebb7297abc7108e3df9a454940d3`
(the same before and after this review). **0 Critical / 0 Major / 5 Minor** (3 new, 2 carried).

No single fault fires the e-match while the bus is disabled. With the bus enabled (from the on-rail check until J400 opens), the
recorded single faults still fire: OUT to GND, a Q124 gate bridge, Q124 failing short. Two more belong in that list (R21-SAF-03).
The round 20 polish changes measure as claimed and add no new neighbour to any pyro or arming net. D-R20-01's residual is as recorded, but
a clean local partial fix exists, checked on a trial copy (R21-SAF-01, fix now).

## Method

- **Inputs.** The committed tree only (`git archive accfff4` into `.supervisor/r21_safety/src`), plus the round 19 board (`50a39de5…`) for diffs.
- **Geometry.** kicad-cli 10.0.7's pcbnew export. Every distance is from my own numpy code, including inner rings and barrel walls.
- **S-8 three ways.** Native polygons, a hole-to-hole check, and my own parser of the fabricated In1 / In2 Gerbers (with net attributes) and the PTH drill file. All three agree.
- **Gates.**
  - Committed S-1 to S-9 and K-actuators: OK.
  - In-memory seeds of S-6, S-8 and route_check's net classes.
  - kicad-cli DRC, all severities, with schematic parity: 0 / 0 / 0.
  - route_check: 0 failing.
- **Fault analysis.**
  - Adjacency inventory of 20 pyro and arming nets (outer 0.5 mm, inner 1.0 mm) on both boards, with a diff.
  - Single-open analysis of 31 safety pin pairs.
  - EN timing corners.
  - The plate model, with C128 added.
  - In2 split spacing.
- **R81 trial.** A trial copy with R81 moved, refilled and re-gated.

## S-8 as built (barrel wall or own inner ring to foreign In1 / In2 copper, mm; native = Gerber)

| Barrel | In1 | In2 | Own inner ring |
|---|---|---|---|
| PYRO1_OUT via (11.630,55.100) | GND 1.021 (ring of the GND partner via; barrel to barrel 1.121) | GND 1.021, 3V3 2.698 | none |
| J121.1 PYRO1_OUT | GND 1.050 | GND 1.050, 3V3 1.061 | none (D-R20-05) |
| J121.2 PYRO1_IGN | GND 0.550, ring 0.251 (exempt) | same; 3V3 ring 3.599 | In1, In2 |
| PYRO1_GATE via (14.4,53.3) | GND 0.251 (exempt) | USB_LIMITED 2.100 | none |
| ACT_GATE vias (16.2,73.3), (11.14,71.7) | GND 1.050 | RAW_PROTECTED 1.050 | none |
| BAT_ENABLE vias (19.675,66.6), (21.3,68.9), (17.1,82.8) | GND 0.251 (exempt) | RAW_PROTECTED / 3V3 1.050 | none |
| J400.2 BAT_SW_RETURN | GND 0.251 (exempt) | GND 1.050, RAW_PROTECTED 1.050 | none (D-R20-05) |

The smallest non-exempt gap is 1.021 mm.

**J1.2 side effect.** In2 RAW_PROTECTED is now 0.251 mm from J1.2's wall. It was already 0.251 mm from the ring that was removed, so the copper-to-copper gap is unchanged. J1.2 joins 40 GND vias already at that hole clearance. A short there is a U9 output short (latch-off part), with no arming or fire path. Closed.

## Findings

**R21-SAF-01 (Minor, carried from R20-SAF-01). EN still hangs on three series vias, but a local fix exists.**
- **Today.** 13 single items separate U9.1 from R81: 3 vias and 10 segments, 20.92 mm of track.
- **Fix.** Move R81 to F(18.848,80.0), rot 0, on the F.Cu EN run. The CAD record itself names this spot.
  - The 13 items drop to 4: one via and 3.89 mm of track.
  - Every other open of the run then leaves EN held low by R81.
  - The GND via (20.706,65.619) can go. It is 0.196 mm from R134.2, the closest RAW_ACT-to-GND approach on the board.
- **Trial copy.**
  - DRC 0 / 0 / 0; route_check 0 failing; silk_check OK.
  - check_r10 33 / 35. Only the hash-bound K-binding and F9-1 fail.
  - No new non-GND neighbour of any pyro or arming net.
- **Records.** The handoff's "not fixable on this board" is overstated.

**R21-SAF-02 (Minor, new). route_check treats the arming-switch chain as an ordinary net.**
- **Gap.** BAT_SW_SOURCE, BAT_SW_RETURN and BAT_ENABLE are not in any R10 critical class, although AGENTS §3 names arming nets as critical.
- **Seed.** Adding the three nets to the class gives 4 failures: the BAT_ENABLE tiny jog at B.Cu (21.0,68.6), and three vias with no GND partner.
- **Fix.** Add the class and the slow-return entry, then record or fix the jog.

**R21-SAF-03 (Minor, new). The enabled-bus single-fault list misses FMEA I-5 and C128.**
- **I-5.** Battery voltage onto 3V3 can make the MCU drive PE4. This has no R10 disposition, and its R6–R9 mitigation (the ARM link) is gone. The bus stays enabled from the on-rail check, so PE4 alone guards the match.
- **R10 geometry.**
  - In2 3V3 borders RAW_PROTECTED for 132 mm, PORT_5V3 for 36 mm and PORT_4V8 for 35 mm, all at 0.300 mm.
  - The unconnected In2 rings of J440.1 and J9.1 sit 0.2505 mm from 3V3.
  - The MCU's VDD absolute maximum is 4.0 V.
- **C128.** This MLCC across Q124 is not named. The plate model gives 991 µε at C128 at 100 g.
- **Fix.** Record both, and tie them to owner row 18. Respin options are listed in the JSON.

**R21-SAF-04 (Minor, carried from R20-SAF-03).** The handoff's per-flight check still says "3V3 at TP81". TP81 is RAW_PROTECTED, B(31.0,84.8).

**R21-SAF-05 (Minor, new). The owner decision table names the wrong board.**
- **Where.** The table and its inventory basis name `50a39de5…` and "rounds 20 and 21".
- **Inventory.** My diff shows the safety inventory carries to `0dc84776…` unchanged, apart from the D-R20-05 ring rows.

## Fix verification

| Fix | Verdict | Note |
|---|---|---|
| D-R20-01 | partly | residual confirmed (13 items); F.Cu partial fix found |
| D-R20-02 | confirmed | no single PORT_4V8 via open (of 9) cuts R402.1 off |
| D-R20-03 | confirmed | U1.74 has no pour connection |
| D-R20-04 | confirmed | TP82 B(11.2,20.7), 1.0005 mm to the pour |
| D-R20-05 | confirmed | no rings at J121.1 / J400.2 (native and Gerber); S-8 seed fails at 0.750 / 0.761 mm |
| D-R20-06 | confirmed | the safety legends are unchanged |
| D-R20-08 | confirmed | no In2 copper in the west aft band |
| D-R20-09 | confirmed | AUX copper ≥ 10.861 mm from pyro and arming copper |
| D-R20-11 | confirmed | 10.65 / 20.47 / 26.41 ms; 8.50 ms at 5.73 V; 6.58 ms at 5.5 V; 10 ms needs 5.917 V; turn-on 30.3–128.6 ms |
| D-R19-01 / -02 / -03 / -04 / -10 | confirmed | 1.021 / 1.050 mm; 0.500 mm; TP121 absent; C123 τ 7.09 µs, off 8.64 µs (25.9 µs after a reset); C87 220 nF |
| D-R19-14, R20-SAF-02, -03 | partly | the board and S-6 are OK (seeded); the TP81 text is not fixed |

## Fix now

1. **R21-SAF-01.**
   - Move R81 to F(18.848,80.0), rot 0.
   - Split the F.Cu EN run at (18.023,80.0).
   - Delete the stub (19.675,66.0)–(19.675,65.0), R81's old GND stub and the via (20.706,65.619).
   - Update FIXED_REFS for R81 and rebuild.
   - C87 stays. If C87 is left far from R81, an intermittent open can let it dump up to 8.4 V onto EN, against a 6.5 V absolute maximum; this is a second-order effect.

Full evidence, rejected candidates and coverage limits: `round21_safety.json`. Scripts and outputs: `.supervisor/r21_safety/`.
