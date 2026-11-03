# Round 21: routing cleanliness and AVA-likeness (Claude)

**0 Critical / 0 Major / 1 Minor (1 new).**
- Target commit `accfff4`.
- PCB `0dc847761de94a45cf68b1c82ec91f38e9d4ebb7297abc7108e3df9a454940d3`, the same before and after the review.
- Full data: [round21_routing.json](round21_routing.json).
- Probe scripts, dumps and renders: `.supervisor/r21_routing/`.

## Gate results on this board (probe copy of accfff4)

- **DRC** (kicad-cli 10.0.7, all severities, schematic parity): 0 violations, 0 unconnected, 0 parity.
- **route_check `--profile r10 --bumps-all`:** 0 failing, 148 information instances, 7 unrecorded leftovers, 45 bump windows.
  - The same checker on `50a39de5…` gives 149.
  - The only difference is that USB_LIMITED's extra_bends instance is gone. Nothing was added.
- **Independent scans on both boards:**
  - Every segment is at 0°, 45° or 90°.
  - No zero-length, dangling, overlap-only or duplicate copper.
  - T-junctions fell from 8 to 6: the two AUX F.Cu taps are gone.
  - Every 45° interior angle sits at a pad centre.
  - No fill piece on any layer lacks a via.
  - Every non-exempt critical via has a GND via within 1.5 mm.
  - The new copper adds no reference-plane change.
- **Detour total:** 116 non-pour nets, 1507.8 mm routed against a 1243.0 mm octilinear spanning tree. The ratio is 1.213×, the same as on `50a39de5…`.

## Round 20 polish changes in this lens

| Fix | Verdict | Measured |
|---|---|---|
| D-R20-02 FB tap via | confirmed | **Via:** (30.575,11.6), inside the one In2 PORT_4V8 fill.<br>**Stub:** a 1.0 mm long, 0.4 mm wide F.Cu run that enters R402.1 at its centre. The record's "0.4 mm" is the width.<br>**Single-via opens:** none of the 9 PORT_4V8 vias, opened alone, cuts R402.1 off U401.1 / .2. On `50a39de5…`, opening (29.75,12.6) did.<br>**GPS_RX_MCU:** the via ring is 0.25 mm from it. The via's In1 void stops 0.09 mm short of the track edge. |
| D-R20-03 U1.74 | confirmed | **Pad:** zone connection NONE.<br>**F.Cu GND:** 14 → 13 pieces, 34 pieces in all, none without a via.<br>U1.74 keeps its run to the via at (17.5,39.3). |
| D-R20-04 TP82 | confirmed | **Spur:** one 6.152 mm segment.<br>**Clearances:** GND fill 1.001 mm, R90 1.075 mm.<br>**Dead end from (15.55,28.0):** 9.10 mm (R18 9.25, R19 12.28). |
| D-R20-05 inner rings | confirmed | **No inner layers:** J121.1 and J400.2.<br>**J1.2:** In1 only.<br>**Walls:** J121.1 is 1.050 mm from GND. J400.2 is 1.050 mm from In2 RAW, and 0.25 mm from In1 GND (exempt, recorded). J1.2 is 0.25 mm from In2 RAW (recorded). |
| D-R20-08 west-aft keep-out | confirmed | **In2 3V3:** −12.507 mm², still one piece.<br>**Band beside the keep-out:** at least 3.2 mm wide.<br>**B.Cu:** no track under the tab. |
| D-R20-09 AUX clamps | confirmed | **Runs:** each B.Cu run is one L into the clamp pad's centre. Each return is 0.7 mm to its own via, which joins F.Cu, In1 and B.Cu GND.<br>**Distances:** pin to clamp along the centre line is 4.08 / 4.18 mm. The record's 3.16 / 3.19 mm is pad edge to pad edge.<br>**Reference:** the stubs run over In2 3V3 only. Via hole to pad edge is 0.25 mm. |
| D-R20-01, -10 | confirmed (as recorded) | The copper is unchanged. |
| D-R19 copper fixes | confirmed | The copper diff shows only the D-R20 changes, so these carry unchanged. |

## Finding

**R21-RTE-01 (Minor, new): the owner-acceptance deviation list is stale.**
- **Header.** `docs/R10_VALIDATION.md` "R10 deviations for owner acceptance" still names `50a39de5…` as "the board" at line 1765, with rounds 20 / 21 planned. The "Inventory basis" at line 1864 names it too.
- **Detour table.** The section 6 table still gives the `a3144b15…` figures (112 nets, 1454.9 / 1195.2 mm, 1.217×), marked "not re-run".
- **Why it matters.** REQUIREMENTS M2 binds the list to the final board's SHA-256.
- **Fix (docs only).** Rebind both lines to `0dc84776…`. Refresh the table to 116 nets, 1507.8 / 1243.0 mm, 1.213×.

## Not filed (see JSON)

- **D440 on the pin-3 row** (Inference):
  - It would make the TX branch one straight segment and save a via.
  - The gain is cleanliness only.
- **AUX_RX jog.** It is forced by the resistor pitch.
- **TP82 spur.** It is now shorter than R18's.
- **R463 text over TP82.** This is silkscreen, for the manufacturing lens.
- **J1.2 / J400.2 at 0.25 mm.** This is recorded and at the DRC floor.
- **Carried items R20-RTE-03, -04, -06, -08 to -11.** The copper is unchanged, and none is worse than recorded.

## AVA comparison

This board is tidier than `50a39de5…`:
- The AUX clamps now sit under J440, as J410's do. Their stubs are simpler (one L, against J410's three-segment runs).
- TP82 sits on a straight spur.
- The U1.74 debris is gone.

Less AVA-like, all unchanged and recorded:
- the GPS double jogs;
- the VLOGIC via loop;
- the USB_FAULT_N and USB_ILIM detours.

## Fix now

R21-RTE-01, docs only, with no board change.

## Limits

- Geometry only: no SI or ESD simulation, and no physical test.
- `tools/check.sh` and `check_r10` were not run.
- The D440 alternative is not DRC-checked.
- D-R20-01 was not re-searched.
