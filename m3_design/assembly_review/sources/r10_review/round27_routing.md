# R10 round 27 — routing lens (Claude)

Target commit `816038c`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (SHA-256 identical
before and after). Probes in `.supervisor/r27_routing/`.

**Totals: 0 Critical / 0 Major / 0 Minor.**

## Findings

None. No AGENTS §3 / REQUIREMENTS M2 rule violation, gate miss, false routing statement or wrong routing calculation
was found on `a0ec075e…`.

## Fix verification

| Change | Measurement | Verdict |
|---|---|---|
| D-R26-01 | GND vias 0.5 / 0.3 mm at (7.4,16.5) / (7.4,20.0), 1.500 mm from J440.3 / J440.4; 0.300 mm to their own pin's pad, 0.800 mm to the neighbour's; in the F.Cu, B.Cu and In1 GND fills. Pins 3 / 4 of J410 / J420 / J440 / J9 flash no inner copper. route_check critical_via_no_gnd 2 (92c3ad59, committed checker) → 0 | confirmed |
| D-R26-02 | C11, R164 and R173 0.65 mm toward y = 0. 3V3A trunk runs through the pad centres. C11.2's return is one 45° diagonal. R13 strap (10.25,52.98)-(9.63,52.98)-(9.2,52.55). PYRO1_OUT's last vertical is (16.87,57.97)-(16.87,58.62) (23.65 → 23.00 mm). PYRO1_OUT to R164.2 1.040 mm; R173.1 to R162.1 0.794 mm, as recorded | confirmed |
| D-R26-04 | R164's 3V3 via at (19.55,55.825) on a 45° strap: 1.065 / 1.081 / 1.0585 mm to R127.1 / R126.1 / R128.1. C10 is at B(17.5,53.5); its return leaves 0.05 mm north of the pad centre. PYRO1_CONT_MID runs (16.87,59.48)-(16.87,60.82)-(17.85,61.8)-(20.83,61.8)-(23.0,59.63)-(23.0,57.83), 10.575 mm, 45° bends only | confirmed |

## Observations (16, not counted)

**Gate runs**
- route_check r10: 0 failing, 5 unrecorded noncritical leftovers, 28 bump windows, right_angle 0.
- Against 92c3ad59 (same checker), three instances changed:
  - the two J440 pad instances are gone;
  - the USB_LIMITED extra_bends instance is re-anchored;
  - the PYRO1_CONT_MID u_turn moved: 10.288 → 10.575 mm.

**Independent scans**
- 90° bends: 35 two-branch 90° nodes, each at a same-net pad or via that covers the inner corner.
- New copper:
  - all of it is octilinear with 45° bends;
  - the R13 and R164 straps are the shortest octilinear paths to their vias.
- Forced or sub-threshold routes:
  - C10.2's 0.05 mm entry offset is below the 0.1 mm threshold.
  - PYRO1_CONT_MID (1.55×) is below the 1.6× gate, and its diagonal is held by Q123.1 at 0.2005 mm.
  - PYRO1_OUT's final vertical is forced by Q124's source via.
- GND partners:
  - the 25 required vias have partners at 0.770–1.492 mm;
  - J440.3 / J440.4 have theirs at 1.500 mm;
  - every unpartnered critical layer change is on AUD-2's slow list;
  - no critical net has inner-layer tracks.
- New vias and pins:
  - every new via is joined to its fills;
  - the 4-position pins 3 / 4 keep no inner rings.
- In2 reference: PYRO1_OUT, PYRO1_GATE and the AUX B.Cu runs each sit over one In2 region. The only voids are their own pin and via voids.
- Near-node scan: these are unchanged from 92c3ad59 (the BUZZ_G T was already noted in the round 24 triage):
  - the BUZZ_G T, 0.02 mm;
  - the VBUS and RAW_PROTECTED Ts, 0.05 mm;
  - C127.1's in-pad piece.
- Under-body vias are unchanged: five 0603, five 1210, and D8.

**Records reproduced**
- Detour table: 116 nets, 1500.8 / 1236.6 mm, 23 nets ≥ +3.5 mm.
  - ACT_FET_S and RADIO_TX_MCU (+3.07 mm each) also fall between +3.0 and +3.5 mm.
  - The text names two nets below the line but does not claim that list is complete.
- Copper counts: 1059 segments, 309 vias (170 GND), 1866.794 mm.
- Probe DRC: 0 copper or clearance violations, 0 unconnected. The library-table warnings are artefacts of the probe directory.
- R10_VALIDATION's historical table still lists the (19.05,55.9) via as "current geometry". It sits under the historical heading bound to b337fe63, so it is a historical record, not a current statement.

## Coverage limits

- Not run (read-only brief): no check.sh, no check_r10, no build.
- Clearances are hand calculations on pad rectangles. They match the recorded figures.
- The probe DRC ran without the schematic or the library table.
- Inherited off-centre pad entries were surveyed only through route_check's output.
- IPC-2152 widths and hazard adjacency are left to the power and safety lenses.
