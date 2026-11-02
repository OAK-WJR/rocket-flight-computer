# R10 round 30 — routing lens (Claude)

Target: commit `0afaed3`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and after.
Read-only; probes in `.supervisor/r30_routing/`. Full evidence in `round30_routing.json`.

## Totals

| Critical | Major | Minor |
|---|---|---|
| 0 | 0 | 0 |

No real error found under the round's strict definition.

## What was checked

- **route_check (profile r10)** on a board copy: 0 failing / 0 allowlisted / 0 stale, 5 unrecorded noncritical leftovers,
  28 bump windows. The current tool fails exactly J440.3 / J440.4 on `92c3ad59…` (3.900 / 4.037 mm) and finds 59
  right-angle bends on `5516eeec…` (B.Cu 31, F.Cu 25, In2 3), as the records say.
- **Independent 45-degree audit** (exact pcbnew shapes): 0 off-angle and 0 zero-length segments out of 1059. All 35
  two-end 90-degree nodes sit in pad or via copper that covers the inner corner. All 8 acute 45-degree branch pairs have
  their wedge apex inside the pad. There are no fold-backs, free ends, overlap-only joints or off-centre via joints.
  C98's GND stitch is the recorded via-on-track-in-fill item.
- **Critical layer changes:** 25 vias, with the nearest GND via 0.770–1.492 mm away. The only two-layer plated pins are
  J440.3 / J440.4, each with its GND partner 1.500 mm away. The In2 rail under these changes and the distance to the
  nearest rail-to-GND capacitor reproduce §6: 23 of 27 changes sit over an In2 power rail, 13 of 21 vias are beyond 4 mm
  from such a capacitor, and C460 is 16.28 / 15.86 mm away.
- **Figures quoted in the docs, all reproduced:**
  - detour table: 116 nets, 1500.8 / 1236.6 mm (1.214×); every row from +3.5 mm up;
  - USB pair: 1.90 / 0.707 mm spacing; trunks 14.70 (D+) / 16.45 (D−) mm;
  - board counts: 1059 / 309 / 170 / 1866.794 mm;
  - the D-R26-02 / -04 clearances;
  - EN run: 3.890 mm;
  - FMEA H-6 surface gaps: 0.200 / 0.200 / 0.330 mm.
- **M2 via-hole rule:** every via hole is at least 0.1 mm from every SMD opening. The only exceptions are the two GAP-3
  VIPPO vias in U401.11.

## Fix verification

| Change | Verdict |
|---|---|
| D-R29-01 / -02 (text, labels, pins only; no routing content) | confirmed, nothing to verify in routing |
| Round 28's J440 clamp correction | confirmed: track 3.864 / 3.964 mm, straight centre to centre 3.157 / 3.194 mm, pad edge to pad edge 1.865 / 1.900 mm, 0.211 mm chamfer cut each |
| D-R26-01 partner vias | confirmed: 1.500 mm from pin centres, 0.300 mm to their own pin's pad, 0.800 mm to the neighbouring pin's pad; no inner rings on pins 3 / 4 |
| D-R24-17 right_angle | confirmed (59 → 0) |
| D-R26-02 / -04 clearances | confirmed |

## Observations (not counted): 12

These are reproductions, plus one method note. The FMEA In2 figure, 132.0 mm of 3V3 edge within 0.6 mm of
RAW_PROTECTED, gives 138.8 mm on its labelled board `0dc84776…` with my sampling and 138.2 mm on `a0ec075e…`. The
difference comes from the measuring method, not from a board change, so no error is shown.

## Coverage limits

- Not re-run: `--bumps-all`, the self-tests, the full `check.sh`, and the K-reference / K-region sampling.
- IPC-2152 widths were checked only on the fire path.
- No physical or return-current measurement was made.
