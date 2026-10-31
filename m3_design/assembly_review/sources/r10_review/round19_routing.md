# Round 19: routing cleanliness and AVA-likeness (Claude)

**0 Critical / 0 Major / 8 Minor (4 new, 4 carried).** Target commit `acba196`. The PCB was
`a3144b151b58daf8ba5747def50decc4d1751ad35be478fafc89ef53aa533918` before and after the review, and after every
CLI run. Full data: [round19_routing.json](round19_routing.json). Probe scripts, renders and the seeded copy are in
`.supervisor/r19_routing/`.

## Gate results on this board

- **DRC:** KiCad 10.0.7, every severity with schematic parity: 0 violations, 0 unconnected, 0 parity.
- **route_check:** the committed checker (`--profile r10 --bumps-all`) reports 0 failing and 139 information
  instances. Against `632a9ad3`, four instances are gone (two at TP121, a 3V3 via-to-GND entry, one collinear
  ordering) and four are new: a 3V3 via (15.7,61.6) now 2.177 mm from GND (was 2.52), a 0.3/0.4 mm width change
  at ACT_FET_S (12.525,71.1), the PYRO1_CONT_MID u-turn, and the reordered collinear entry.
- **K-reference:** compared with `632a9ad3`, no samples are lost and none are newly unreferenced.
- **check_r10:** S-3, S-8, LC-1, M-6, K-reference, K-region and K-plane all pass.

## The round 18 fixes

| Fix | Verdict | What was measured |
|---|---|---|
| D-R18-01 (copper) | partly | The divider copper and its 3 vias are gone, and the B.Cu pour refills cleanly. It leaves a new F.Cu GND fragment at U1.19 (R19-RTE-01). |
| D-R18-02 | confirmed | Geometry exact. ACT_GATE B.Cu 7.239 → 14.817 mm. TP pad to GND fill 1.0005 mm. M-6 margins 1.835 / 2.98 mm. Via hole 0.18 mm from R119.1. My own legal-spot search saves at most about 1.2 mm. |
| D-R18-03 | partly | Every ACT_EN_MCU figure reproduces (0.550 / 0.520 / 0.670 / 0.425 / 0.330 mm). Not recorded: BAT_FAULT_N now sits 0.180 mm from GND via (27.9,64.25) (was 0.650) and 0.380 mm from 3V3 via (28.1,60.0) (was 0.850). |
| D-R18-04 | confirmed | All six barrels are 1.050 mm from foreign inner copper. Only slow and power nets cross the new holes. In1 GND is still one piece. |
| D-R18-05 | confirmed | Every gap reproduces; OUT to R134.2 reads 2.830 mm (pad polygon approximation). PYRO1_OUT is 9.5 mm shorter. The MID u-turn is forced by the buzzer cell. |
| D-R18-06 | confirmed | The 3V3 fill is one piece, 1466.52 mm². Necks: about 0.52–0.55 mm (island A and the bay) and about 0.45–0.48 mm (finger), against the record's "about 0.55 / 0.50". |
| D-R18-07 | confirmed | SD_MOSI 36.099 → 34.104 mm, 12 → 10 segments. The 0.5 mm MOSI–SCK parallel run is gone. |
| D-R18-08 (track entries) | confirmed | Both tracks end at the new L400 pad centres. |

## Findings

**R19-RTE-01, Minor, new: a GND pour fragment with no via.** Removing V3V3_SENSE (together with moving BAT_FAULT_N)
leaves a 1.693 mm² F.Cu GND fragment:

- **Where:** x 25.12–27.15, y 51.24–53.45, hanging off U1.19's pin tip.
- **Shape:** no via, and only the U1.19 pin connects it. Its tongue is 0.39 mm wide between ACT_EN_MCU and BAT_FAULT_N.
- **Gate:** route_check's pour_finger test looks only at pieces longer than 3 mm, so nothing reports it.

Electrically it is harmless; it is new pour debris.

**R19-RTE-02, Minor, new: TP121's ACT_GATE arm.** TP121 sits at B(4,70) at the end of a 7.14 mm ACT_GATE stub.

- **Needed?** Yes, under TP121's own rules. An independent search applied the 1.0 mm test-pad clearance, the
  courtyard, M-6 and the board edge. The best B.Cu alternatives are B(4.39,70.0) (0.39 mm shorter) and
  B(5.3,70.8) (1.0–1.2 mm shorter, but with a bend). No F.Cu spot comes within 6 mm.
- **Cost:** ACT_GATE's outer copper doubles, all at the 0.25 mm pour clearance to GND.
- **Records:** M3_R10 records the stub; R10_VALIDATION §6, the owner's M2 list, does not.
- **Owner option:** drop TP121 and probe ACT_GATE at C120.2 or R119.1, as D-AUD-05 already did for six other probes.

**R19-RTE-03, Minor, new: incomplete records.** Two round 18 records do not match this board:

- BAT_FAULT_N's two new neighbours (0.180 and 0.380 mm) are not in D-R18-03.
- The §6 per-net table still shows PYRO1_OUT at 33.1 / 22.0 mm; on this board it is 23.65 / 15.72. MID is now
  10.50 / 7.08 and ACT_GATE 20.54 / 17.08. The row is also unchanged in the later commit `1e60441`.

**R19-RTE-04, Minor, new (missed by rounds 1–18): vias under resistor bodies.** Six 0603 resistors (R86, R89,
R91, R101, R401, R403) have a fanout via centred between their pads, 0.175 mm from both. On R101 the via belongs to
a third net, CAM_UART_OE. This is an untidy pad entry and cannot be inspected under the part; the electrical effect
of a bridge is small (Inference). It is not recorded anywhere.

**Carried (re-checked: the copper did not change):**

- R19-RTE-05 (R18-RTE-02): layer-change returns over the In2 power rails.
- R19-RTE-06 (R18-RTE-03): detours. Refreshed: 1454.9 / 1195.2 mm, 1.217×.
- R19-RTE-07 (R18-RTE-05): the USB pair is not routed as a coupled pair.
- R19-RTE-08 (R18-RTE-06): copper under U4's body.

## AVA comparison

**Tidier than on `632a9ad3`:**

- PYRO1_OUT is 9.5 mm shorter and no longer threads between R134.2 and Q123.
- SD_MOSI is straight.
- Four vias are gone.

**Less AVA-like:**

- TP121's arm runs out to the board edge, where AVA probes at part pads.
- The CH1 sense bank is no longer a repeated column: R173 sits 6.1 mm west, and MID wraps 10.5 mm around the buzzer.
- The U1.19 GND fragment.

## Fix now

None of these needs CAD now, and any board change restarts the clean pair. If CAD reopens for another reason, set
U1 pad 19's zone connection to NONE in `r10_pcb.py`. I checked this on a probe copy:

- The fragment, and only the fragment, disappears.
- route_check, the check_r10 subset and DRC are unchanged.
- Library parity is still to be confirmed in the canonical build.

The records items in R19-RTE-02, -03 and -04 can be fixed now without touching the board.

## Limits

This was a CAD geometry review only. Not done: field solve, current analysis of the necks, full check.sh, and any
physical test. The legal-spot search ignores legend fit and probe access. The assembly consequences in R19-RTE-04
are Inference. No other round 19 material was opened.
