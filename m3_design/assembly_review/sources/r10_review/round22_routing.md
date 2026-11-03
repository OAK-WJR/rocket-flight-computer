# Round 22: routing cleanliness and AVA-likeness (Claude)

**0 Critical / 0 Major / 1 Minor (1 new).**
- Target commit `ec8cb98`.
- PCB `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1`, the same before and after the review.
- Full data: [round22_routing.json](round22_routing.json).
- Probe scripts, dumps and images: `.supervisor/r22_routing/`.

## Gate results on this board (probe copies)

- **DRC** (kicad-cli 10.0.7, all severities, schematic parity, refill): 0 violations, 0 unconnected, 0 parity issues.
- **route_check `--profile r10 --bumps-all`:** 0 failing, 148 information items, 6 unrecorded leftovers, 45 bump windows.
  - The same checker on `0dc84776…` fails 1: the old 0.424 mm BAT_ENABLE tiny jog.
  - Item diff: two removed (BAT_ENABLE `extra_bends` and `tiny_jog`) and two added (`pad_end_offcentre` at U2.1, 0.35 mm, and `power_via_no_gnd` at (23.0,70.0), 2.182 mm), exactly as the fix record says.
- **check_r10, selected rules:** S-8, K-reference, K-region, K-plane, K-copper, K-power and K-inner all OK.
- **Independent scans over all 983 segments and 300 vias (167 GND, 1871.612 mm of track):**
  - Every segment runs at 0°, 45° or 90°, with no arcs.
  - No zero-length segments, duplicates, contained overlaps or overlap-only tees.
  - Every via connects at least two layers.
  - There are no acute angles outside pads.
  - The 11 tees are unchanged.
  - One track end sits on a pad edge: L1.2 at (24.2,77.0), recorded in R14.
- **GND partner vias:** every one of the 25 non-exempt critical vias has a GND via within 1.5 mm. The worst is PYRO1_GATE at 1.492 mm. The BAT_ENABLE vias are at 2.902, 1.875 and 1.866 mm; the chain is AUD-2 exempt.
- **Fast-net references:** each fast net runs over one plane net per layer, the same on both boards. Section 6's figure is confirmed: 21 of 25 required vias sit over an In2 rail (3V3 17, PORT_4V8 4).

## Round 21 fixes

| Fix | Verdict | Measured |
|---|---|---|
| D-R21-01 (inner PTH hole clearance 0.55 mm) | confirmed | All 31 plated pads are at least 0.550 mm from foreign In1 / In2 fill. Inner copper changed only at three places: the J400.2 In1 annulus, the J1.2 In2 annulus and eight In2 3V3 lunes at J3's shell slots. The neck census is identical on both boards, so nothing splits. The JLC page, re-read, gives 0.3 mm for this clearance. |
| D-R21-02 (U2.1 second path) | confirmed | 1.485 mm, 0.4 mm wide, at 45°. Both U2.1 vias land in the one In2 3V3 fill. L1.2 has two routes to the rail. The off-centre start is a centred entry whose 0.35 mm vertical piece lies inside the pad. No new GND island. |
| D-R21-04 (BAT_ENABLE hop) | confirmed | The hop is now 1.449 / 0.675 / 0.849 mm, above the jog thresholds. I seeded a one-segment hop with its via at (19.0,66.6): it fails DRC against TP120's 1.0 mm (0.9607 mm). Every 45° line into (21.3,68.9) is that same line, so the recorded shape is the legal one. |
| D-R21-05 (R81 / C87 at U9) | confirmed | The diff shows exactly the stubs and vias recorded as removed. U9.1 → C87.1 is 2.013 mm and U9.1 → R81.1 is 3.889 mm, over one via. Both pads 2 sit in F.Cu GND piece 1, which has 2 vias. The pour regained at the old spot joins well-stitched pieces: F.Cu GND has 13 pieces before and after. |
| D-R21-06, D-R19-02, D-R20-01 | confirmed | K-plane is OK and the fills under the tabs are unchanged. The D-R19-02 via and its keep-out are unchanged. One EN via remains, as recorded. |

## Detour table (section 6)

Recomputed with independent code: routed length against the octilinear MST of pad centres, over non-pour nets.

| Board | Nets | Routed (mm) | MST (mm) | Ratio |
|---|---|---|---|---|
| `5516eeec…` | 116 | 1505.5 | 1236.9 | 1.217× (+268.6 mm) |
| `0dc84776…` | 116 | 1507.8 | 1243.0 | 1.213× (round 21's figure) |

- **The docs' 116 nets / 1505.5 / 1236.9 mm / 1.217× is right**, and every table row matches to 0.01 mm.
- BAT_ENABLE's excess rose from +4.5 to +8.2 mm, though its routed length fell from 27.93 to 25.58 mm. Its MST shrank because R81 and C87 now sit beside U9.
- The remaining excess is forced by placement:
  - The run must pass north of Q122's GND via and stub at x 17.8.
  - It must cross under the F.Cu ACT_EN_MCU diagonal.
  - The leg from (21.3,68.9) to R81.1 is already the octilinear minimum.

## Finding

**R22-ROUTING-01 (Minor, new): the section 6 table is titled "the largest excesses" but leaves out nine larger ones.**
- **What it lists.** ACT_GATE (+3.9 mm) ranks 20th and PYRO1_CONT_MID (+3.4 mm) ranks 25th.
- **What it leaves out:**
  - VLOGIC +5.69 mm
  - CAM_PWR_EN +5.66 mm
  - CAM_FAULT_N +5.30 mm
  - SERVO2_MCU +5.06 mm
  - SERVO1_MCU +4.66 mm
  - SERVO3_MCU +3.90 mm
  - QSPI_IO2 +3.69 mm
  - USB_DM +3.52 mm
  - ACT_EN_MCU +3.51 mm
- **Coverage.** The table covers 165.6 of the 268.6 mm excess.
- **Second gap.** Section 6's list of counted items for the current board leaves out R89's via `power_via_no_gnd` (2.182 mm). D-R21-02 does record it.
- **Fix (docs only).** Retitle the table "largest excesses plus the pyro / arming nets", or add the nine rows. Add the R89 via item to the counted list.

## AVA comparison

**Tidier than `0dc84776…`:**
- The EN pull-down and filter now form a local cell at U9, with pads on the run and returns into U9's own GND via, as AVA's local cells do.
- The jog and the stub corner are gone.

**Still less AVA-like (placement, recorded):**
- the BAT_ENABLE eastward excursion with 3 vias (1.47×);
- the GPS double jogs;
- the VLOGIC via loop;
- the USB_FAULT_N and USB_ILIM detours.

## Not filed (see JSON)

- The one-segment hop (fails DRC).
- The U2.1 off-centre start and its parallel via pair.
- R89's via without a GND partner (a power via).
- The narrowed plane strips. No splits; the 0.379 mm strip is far above JLC's 0.09 mm.
- The L1.2 edge end (recorded in R14).
- The USB_DM A7 / B7 tie (carried).
- Carried items R20-RTE-03 / -04 / -06 and R19-RTE-03 / -04. Their copper is unchanged.

## Fix now

R22-ROUTING-01: text only, with no board or check change.

## Limits

- Geometry only: no SI, ESD or physical test.
- Full `tools/check.sh` and full `check_r10` were not run.
- J3 slot clearances are taken as centre-to-copper distance minus the slot half-width.
- The U2.1 in-line via rejection is taken from the record; I did not re-seed it.
