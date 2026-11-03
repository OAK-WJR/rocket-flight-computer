# R10 round 26 — routing lens (Claude)

Target commit `3d8e845`, board `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f` (SHA-256 identical
before and after). Probes in `.supervisor/r26_routing/`.

**Totals: 0 Critical / 0 Major / 3 Minor.**

## Findings

**R26-ROUTING-01 (doc, Minor): six 0603 under-body fan-out vias are now five.** Owner row 8 (bound to `92c3ad59…`),
section 6 R19-RTE-04 ("owner M2 list") and REQUIREMENTS M2 still name six, R403 F(31.4,14.4) included. D-R24-09 moved
R403 to B(30.9,14.6) and removed that via: no via lies within 0.9 mm of R403's body, and its GND returns on B.Cu to
U401.4. A scan of every 2-pad part finds five 0603 resistors with a via between the pads (R86, R89, R91, R101, R401);
the same scan finds six on `a3144b15…` and `5516eeec…`. Fix: row 8 "five … (R403's went with D-R24-09)"; annotate
R19-RTE-04 and M2.

**R26-ROUTING-02 (doc, Minor): "12 of the 21 are beyond 4 mm" is 13.** Section 6 "Layer-change returns". With the metric
that reproduces every quoted figure (via centre to the rail-side pad of the nearest same-rail-to-GND capacitor: range
1.29–6.19, SD 6.19 / 5.33 / 5.07 / 4.84, SPI1 5.04–5.77, QSPI_NCS 5.32, RADIO_TX 5.12), 13 vias are beyond 4 mm.
CAM_MCU_RX is 4.02 mm from C29.1, CAM_MCU_TX 4.21 mm and GPS_RX_MCU 4.33 mm. Centre to centre gives 12, but then SD_MISO is
6.10 mm. The board of round 18 gives the same result. Fix: 13 (also in the R18-m21 row).

**R26-ROUTING-03 (rule, Minor; gate gap): J440's UART wires change layer through the pins with no GND via within
1.5 mm.** AUX_TX_WIRE runs F.Cu from R471 to J440.3, then B.Cu to D440.1. AUX_RX_WIRE does the same at J440.4 to D441.1.
The plated pins are the only layer change of either net, and the nearest GND via is 3.900 / 4.037 mm away. D-R19-15
keeps "the GPS / RADIO / AUX / CAM port UART nets under the stricter 1.5 mm GND-partner-via … rules … the frozen board
meets them", and route_check's R10_CLASSES (the M2 R10 gate) class them as critical signal nets. This is new against the
round 24 / 25 triage observation, which did not weigh D-R19-15. D-R20-09 created the layer change when it put the clamps
under J440 on B.Cu; before that the AUX pair was F.Cu only. route_check passes because critical_via_no_gnd tests only
via items. Fix: route both J440 runs on B.Cu from R470 / R471 (as at J410 / J420, where a via can take a partner), or
record the two pins as an owner deviation with a reason. In the gate, count a plated pad that carries one critical
signal net's tracks on two layers as a layer change.

## Fix verification

| Change | Measurement | Verdict |
|---|---|---|
| D-R24-17 | right_angle 59 on `5516eeec…` (B 31 / F 25 / In2 3) → 0; all 1057 segments octilinear; J440 clamp runs 3.864 / 3.964 mm; USB_DM −0.422 mm | confirmed |
| D-R24-18 | BAT_ENABLE via to BAT_FAULT_N: legs 0.200, chamfer 0.2015 mm | confirmed |
| D-R24-09 | R402 / R403 on B.Cu, four vias gone, OUT via (29.75,11.65), T 0.075 mm inside R402.1 | confirmed (records: R26-ROUTING-01) |
| D-R24-02 / -03 / -04 / -07 / -08 / -10 / -15 | all named second / moved vias present, (21.1,79.1) absent | confirmed |
| D-R24-11 | D402 tap 4.114 mm, GND leg 0.70 mm | confirmed |

## Observations (14, not counted)

- route_check 0 failing, 5 unrecorded leftovers and 27 bump windows. The 25 required vias have GND partners at
  0.770–1.432 mm, all joined to In1 GND. The 21-of-25 In2-rail figure and the detour table (1501.8 / 1237.8 mm) reproduce.
- The reference sampling is clean apart from the antipads and the S-8 voids. The USB pair figures reproduce. The new
  D-R24 copper keeps ≥ 0.150 mm to foreign copper.
- Row 8's "ten nets" is round 18's top-ten summary; the cited table lists 23.
- D8 has a GND fan-out via between its pads at (16.05,75.0) that the under-body lists do not include. This is a review
  item; the final list is not yet due.
- Row 30's distances are labelled for `5516eeec…`; on this board they are 2.791 / 6.713 mm.
- The information counts on this board have no summary yet (pad_end_offcentre 70, segment_inside_pad 27, short_layer_hop
  18, power_via_no_gnd 28 …).
- The BUZZ_G / VBUS T offsets are as in the round 24 triage.
- The U401 T alternatives (0.085 / 0.057 mm), R19-RTE-03, R20-RTE-04 and R20-RTE-06 reproduce.

## Coverage limits

No full `tools/check.sh` or DRC run (read-only). The section 6 diagnostic-router recoveries were not re-run. Pad-entry
tidiness was surveyed through route_check's information output. IPC-2152 widths are left to the power lens.
