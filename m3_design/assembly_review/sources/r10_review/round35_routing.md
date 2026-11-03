# R10 round 35: routing lens

Target `c3c4249`, board `a0ec075e…` (SHA-256 identical before and after). Reviewer: Claude.

**Totals: 0 Critical / 0 Major / 0 Minor.** No real errors found.

## Checks run
- `route_check --profile r10` on a copy: 0 failing, 0 allowlisted, 0 stale; 5 non-critical leftovers (informational).
- An independent scan of all 1059 segments found 0 arcs, 0 off-45° headings and 0 sharp bends in open copper. There are 35 90° bends at pads or vias, and in each the inner corner lies inside the pad or via copper.
- Independent GND partner check on all 34 critical-net vias. All are within 1.5 mm except nets on AUD-2's slow-return list. The worst non-exempt via is PYRO1_GATE at 1.492 mm.
- J440 clamp figures match the board. Centre to centre: 3.157 / 3.194 mm. Track: 3.864 / 3.964 mm. Pad edge to pad edge: 1.865 / 1.900 mm. The partner vias are 1.500 mm from their pins, 0.300 mm from their own pad and 0.800 mm from the neighbouring pad.
- The C88 and BAT_IN via positions match the D-R24-17 row.

## Observations (not counted): 4
The informational leftovers, the Q124.2 pass-through, the INFO entries for power vias without a GND partner, and the slow-return exemptions. Details are in the JSON.

## Fix verification
R34-TRI-01 is text-only and outside this lens.
