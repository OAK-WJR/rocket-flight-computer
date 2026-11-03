# R10 round 28: routing lens (Claude)

- **Target:** commit `19dd0b5`, board `a0ec075e…`. SHA-256 is `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and after the review.
- **Method:** read-only. Probes are in `.supervisor/r28_routing/`. Machine-readable copy: `round28_routing.json`.

## Totals

**0 Critical / 0 Major / 0 Minor real errors.**

## Findings

None. I re-measured every routing rule in AGENTS §3 and REQUIREMENTS M2 independently of route_check, and I checked the routing figures the current docs quote. Nothing violates a rule, and no figure is false.

## What was checked (observations, not counted)

**route_check (profile r10) on a probe copy**
- 0 failing, 0 allowlisted, 0 stale and 28 bump windows.
- 5 unrecorded noncritical leftovers: BAT_OVLO, three tiny jogs (BUZZ_DRV, BAT_FAULT_N, I2C1_SDA) and the USB_ILIM detour.
- With `--bumps-all`: pad_end_offcentre 70 and segment_inside_pad 27, as in R10_VALIDATION:2095. The category summary for the final board is not due yet.

**45° rule**
- Independent scan: 0 arcs, 0 off-angle segments, 0 dangling ends.
- Bends: 467 are 135°, 35 are 90° and 4 are 45° interior. Every 90° and 45° bend sits at a same-net pad or via whose copper covers the inner corner (pcbnew shape test).

**GND partner vias**
- There are 27 return-required layer changes: 25 vias plus J440.3 / J440.4. Each has a GND via 0.770 to 1.500 mm away.
- No other plated pin carries a return-required critical net on two layers.
- All 170 GND vias tie to the In1 GND fill.

**Reference planes**
- F.Cu critical tracks run over In1 GND only.
- Each B.Cu critical track runs over a single In2 net. The only gaps are its own antipads and pads, plus the recorded PYRO1_OUT barrel keep-outs.

**Doc figures reproduced exactly**
- R10_VALIDATION §6:
  - the detour table: 116 nets, 1500.8 / 1236.6 mm, 1.214×, all 23 rows;
  - the layer-change return figures: 21 of 25 vias over In2 power (3V3 ×17, PORT_4V8 ×4), capacitors 1.29–6.19 mm away, 13 of 21 beyond 4 mm, C460 16.3 / 15.9 mm, B.Cu–In2 0.203 mm and B.Cu–In1 1.263 mm;
  - the USB pair: 1.90 / 0.707 mm and 16.45 / 14.70 mm.
- M3_R10:
  - the contents row: 1059 segments, 309 vias, 1866.794 mm of track;
  - the J440 clamp runs: 3.864 / 3.964 mm.
- ORDERING:650: D402's 4.114 mm tap and its GND via 0.700 mm away.
- Owner rows 8 and 24: 0.180, 0.200, 0.330 and 0.200 mm.
- C89: 0.186 mm.
- The R402.1 T: 0.075 mm inside the land.
- In2 3V3 fill: 1430.05 mm².

**Recorded or outside the rule**
- Under-body vias: the scan finds only items that are already recorded.
- The 26 A-B-A lane-shift jogs: each middle is at least 0.5 mm with an offset of at least 0.25 mm, so they fall outside the tiny_jog definition. The GPS jogs are recorded (R20-RTE-03), and LED_YEL's middle is exactly 0.500 mm.
- The GND overlap stitch at (23.8,62.95) is the recorded C98 stitch.

## Fix verification

| Change | Verdict | Measurement |
|---|---|---|
| D-R26-01 | Confirmed | GND vias 1.500 mm from J440.3 / .4. Each is 0.300 mm from its own pin's pad and 0.800 mm from the neighbouring pin's, and sits in the F / In1 / B GND fills. route_check passes the pins. |
| D-R26-02, routing part | Confirmed | R13's via and C11.2's return turn at 45°. No new bend or off-angle segment. |
| D-R26-04, routing part | Confirmed | R164 strap at 45°. C10.2's stub is 0.05 mm off the pad centre. PYRO1_CONT_MID's diagonal and its 10.57 / 6.81 mm match the records. |
| D-R27-01 … -03 | Confirmed, no routing effect | Board unchanged. |
| R27-TRI-03 | Confirmed | In2 3V3 is 1430.05 mm², one piece. |

## Coverage limits
- No gate seeds were run. The rules were re-measured independently instead.
- I checked the review-only M2 items against the records. I did not judge each one for removability.
- I did not re-derive the IPC-2152 sizing (K-power) or signal integrity.
