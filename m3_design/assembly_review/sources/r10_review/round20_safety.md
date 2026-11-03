# Round 20 safety review (Claude)

Target commit `6628488cf34bf33bdf104cb4383fcbe447c5da65`, PCB `50a39de5b76dec3cb58bbb1b0ab528fd4d65098de9dfe8f89f49e2e7adcbd976`
(the same before and after this review). **0 Critical / 0 Major / 5 Minor** (4 new, 1 carried).

No single fault fires the e-match while the bus is disabled. With the bus enabled, the only single faults that fire are the
recorded ones: OUT to GND, a Q124 gate bridge, and Q124 failing short. The round 19 fixes measure as claimed. Two arming-switch
gaps are new:
- U9's EN pin hangs on three series vias.
- The new AUX port's leads and nets fall outside the port-isolation gate and the harness rules.

## Method

- **Inputs.** The committed tree only (`git archive 6628488` into `.supervisor/r20_safety/src`).
- **Geometry.** pcbnew 10.0.7 geometry export. Every distance is from my own numpy code, including unflashed via and hole barrels.
- **S-8, three ways.**
  - Native polygons.
  - A copy refilled by kicad-cli (identical result).
  - My own parser of the fabricated In1/In2 Gerbers and the PTH drill file (exact match).
- **Other checks.**
  - Committed S-3, S-5, S-6 and S-8 on the board: all pass.
  - Native DRC with schematic parity: 0 / 0 / 0.
  - Adjacency inventory of 18 pyro and arming nets, on this board and on `a3144b15`, with a diff.
  - Single-open connectivity of nine safety nets.
  - A seeded S-6 test.
  - EN timing calculation, including the TPS25947 EN leakage.
  - BOM and CPL rows for the safety parts.
- **Datasheets.** TI SLVSFC9C p5 and p9; AOS AON7524 Rev 1.1 p2; AO3400A Rev 3.1 p2.

## S-8 as built (barrel wall / own inner ring to foreign In1-In2 copper, mm)

| Barrel | In1 | In2 | Ring |
|---|---|---|---|
| PYRO1_OUT via (11.630,55.100) | GND 1.021 | GND 1.021, 3V3 2.698 | none |
| J121.1 PYRO1_OUT | GND 1.050, 3V3 barrel 1.320 | GND 1.050, 3V3 1.061 | GND 0.750, In2 3V3 0.761 |
| J121.2 PYRO1_IGN | GND 0.550 (exempt) | GND 0.550 | GND 0.251 |
| PYRO1_GATE via (14.4,53.3) | GND 0.251 (exempt) | USB_LIMITED 2.100 | none |
| ACT_GATE vias (16.2,73.3), (11.14,71.7) | GND 1.050 | RAW_PROTECTED 1.050 | none |
| BAT_ENABLE vias (19.675,66.6), (21.3,68.9), (17.1,82.8) | GND 0.251 (exempt) | RAW / 3V3 1.050, GND ≥ 1.123 | none |
| J400.2 BAT_SW_RETURN | GND 0.550 (exempt) | GND 1.050, RAW_PROTECTED 1.050 | 0.750 / 0.750 |

The minimum is 1.021 mm. The closest hole to a protected hole is the GND partner via, 1.121 mm hole wall to hole wall from the OUT via.

## Findings

**R20-SAF-01 (Minor, new). U9's EN pin depends on three series vias.**
- **Where.** U9.1 reaches its only pull-down, R81 (with C87 beside it), through three vias in series, (19.675,66.6), (21.3,68.9) and (17.1,82.8), and about 20 mm of 0.2 mm track. Opening any one of those vias, or any one of 10 track segments, floats EN. TI says of EN: "Do not leave floating" (p5).
- **Which way it drifts.** The floating island sits 0.200 mm from BAT_IN (U9.5) and 0.200 mm from BAT_OVLO (about 0.9 V). There is no GND within 0.6 mm. So it drifts toward ON (Inference): the board can come on, or stay on, with J400 open.
- **Coverage.** The gate networks of Q120 to Q124 have no via dependence. Round 19's single-open analysis did not cover this net.
- **Fix.** Put the pull-down at the pin: R81 on B.Cu beside U9.1, with no via between them. Any open in the J400 run then leaves the board off. If there is no legal spot, record this as a respin item.

**R20-SAF-02 (Minor, new). S-6 cannot see the AUX nets or the EN chain.**
- **Gaps.** S-6's `PORT_NET` has no `AUX_` prefix. Its `SAFE_NET` omits the arming-switch chain, BAT_ENABLE and BAT_SW_*.
- **Seeded test.** I placed a track 0.100 mm from PYRO1_OUT. On an AUX net it passes S-6; the same track on a GPS net fails.
- **This board.** AUX copper is at least 27.7 mm from every pyro and arming net, so nothing is violated today.
- **Overstated records.** FMEA I-11 claims more than the gate checks. The S-8 header and docstring are stale.
- **Fix.** Add `AUX_` to `PORT_NET` and `BAT_ENABLE|BAT_SW_` to `SAFE_NET`, add the seeded tests, and correct the text.

**R20-SAF-03 (Minor, new). The harness rules miss the AUX leads.**
- **Where.** J440's four leads leave the same west face as the J121, J400 and J1 leads. The dress rules separate J400 only from battery and servo power leads.
- **What a chafe does** (Calculation):
  - J440.1 (4.8 V) or J440.3 (TX idling high) onto the J400.2 lead holds EN at 1.81–1.87 V or 1.27–1.28 V. Both are above the 1.116 V falling threshold, so J400 cannot turn the board off.
  - A self-powered module's TX on J440.4 gives about 1.27–1.29 V, which turns the board on with J400 open.
  - J440.2 (GND) onto the E1− lead (J121.1) bypasses Q124 and fires an enabled match.
- **Other text gaps.** The e-match rule lists only "GPS, radio, camera" modules. The handoff says "3V3 at TP81", but TP81 is RAW_PROTECTED.
- **Fix.** Twist the J121 pair and the J400 pair, each on its own ties, apart from the J440 leads. Name any module on J410, J420, J440 or J9 in the e-match rule. Correct the TP81 wording.

**R20-SAF-04 (Minor, new). The C87 worst case leaves out the EN leakage.**
- **Reproduced.** The D-R19-10 figures check out.
- **With leakage.** Adding IENLKG ±0.1 µA (p9) gives a worst drop-out immunity of 10.6 / 20.5 / 26.4 ms at 6.0 / 7.4 / 8.4 V and a turn-on of up to 129 ms.
- **Margin.** The proposed 10 ms chatter criterion needs a pack voltage of at least 5.92 V. At 5.5 V the immunity is 6.6 ms.
- **Disarm.** This improves: U9 turns off within 57 ms of J400 opening (it was about 0.57 s with 2.2 µF).
- **Fix.** Restate F6 with the leakage term, then either set the criterion against the minimum loaded pack voltage or raise C87.

**R20-SAF-05 (Minor, carried from R19-SAF-05). The terminal inner rings are still 0.75 mm from hazardous copper.**
- **J121.1.** Its inner ring is 0.750 mm from In1/In2 GND and 0.761 mm from In2 3V3. The 3V3 figure was 0.804 mm: the 3V3 fill now reaches the new keep-out edge.
- **J400.2.** Its inner ring is 0.750 mm from In2 RAW_PROTECTED.
- **Disposition.** This is owner table row 9.
- **Fix.** Remove J121.1's and J400.2's unconnected inner pads (a board pad override, as for U1.19). The figures then become 1.050 / 1.061 / 1.050 mm.

## Round 19 fix verification

| Fix | Verdict | Note |
|---|---|---|
| D-R19-01 (PYRO1_OUT keep-outs) | confirmed | 1.021 / 1.050 / ring 0.750 mm by three methods; fills one piece; side effect: J121.1 ring to 3V3 0.804 → 0.761 mm |
| D-R19-02 (BAT_ENABLE via) | confirmed | 0.300 → 0.500 mm to R134.2; In2 RAW 1.050, GND 0.993 → 1.123 mm |
| D-R19-03 (TP121 removed) | confirmed | ACT_GATE within 0.30 mm of GND: 12.915 → 7.992 mm; ACT_GATE to BAT_SW_SOURCE 0.469 mm |
| D-R19-04 (C123) | confirmed | τ 7.09 µs; on 7.6 µs, off 8.6 µs, reset 25.9 µs; Miller 35 mV; only GND neighbours |
| D-R19-10 (C87 220 nF) | partly | numbers reproduced; EN leakage omitted (R20-SAF-04) |
| D-R19-14 (AUX port) | partly | no on-board path (≥ 27.7 mm, no shared part); S-6 and harness gaps (R20-SAF-02, -03) |
| Surface inventory reused from `a3144b15` | confirmed | the same 76 outer pairs; only the fix deltas differ |

## Fix now

1. **J121.1 and J400.2.** Remove the unconnected inner pads (R20-SAF-05).
2. **S-6.** Extend the regexes and add the seeded tests (R20-SAF-02).
3. **R81.** Move R81 (and C87) beside U9.1, with no via between them, if a legal spot exists (R20-SAF-01).
4. **Docs.** Fix the harness and e-match wording, the TP81 net name, and F6's EN figures (R20-SAF-03, -04).

Full evidence, the rejected candidates and the coverage limits are in `round20_safety.json`. The scripts and outputs are in `.supervisor/r20_safety/`.
