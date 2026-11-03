# Round 20: routing cleanliness and AVA-likeness (Claude)

**0 Critical / 0 Major / 11 Minor (7 new, 4 carried).** Target commit `6628488`. The PCB was
`50a39de5b76dec3cb58bbb1b0ab528fd4d65098de9dfe8f89f49e2e7adcbd976` before and after the review. The full data is in
[round20_routing.json](round20_routing.json). Probe scripts, renders and the archive copy are in `.supervisor/r20_routing/`.

## Gate results on this board (probe copy of 6628488)

- **DRC:** kicad-cli 10.0.7, all severities, with schematic parity: 0 violations, 0 unconnected, 0 parity.
- **check_r10 (full contract) and fit_check:** OK. This includes K-reference, K-region, K-plane, K-power and S-8.
- **route_check `--profile r10 --bumps-all`:** 0 failing, 149 information instances and 7 unrecorded leftovers. The
  same checker on `a3144b15` gives 140 instances and 6 leftovers.
  - **11 instances added:**
    - USB_FAULT_N detour, ratio 1.62. This is a new leftover.
    - extra_bends on GPS_TX, GPS_RX and USB_LIMITED.
    - Five short layer hops: the BAT_ENABLE hop and four second-via stubs.
    - Two power_via_no_gnd.
  - **1 instance removed:** R90.2's off-centre pad entry.
- **Independent scans:**
  - Every segment is at 0, 45 or 90 degrees.
  - No duplicate, zero-length, dangling or overlap-only ends.
  - Two new T-junctions, both AUX ESD taps. Other ports' wires use the same style.

## The round 19 fixes in this lens

| Fix | Verdict | Measured |
|---|---|---|
| D-R19-01 PYRO1_OUT keep-outs | confirmed | **Barrel walls:**<br>• OUT via to In1 / In2 GND fill: 1.050 mm. To its own partner-via ring: 1.021 mm.<br>• J121.1: 1.050 mm to GND, 1.061 mm to In2 3V3.<br>**Plane continuity:**<br>• Both planes stay one piece at a 0.5 mm opening.<br>• In2 GND_CH1 now has a dead-end finger with a 0.60 mm neck (R20-RTE-07). |
| D-R19-02 BAT_ENABLE via | confirmed | • 0.500 mm to R134.2. F.Cu 1.556 mm.<br>• GND partner 1.423 mm. The hop is needed to cross ACT_EN_MCU.<br>• "In2 GND 1.123" is barrel to barrel to the GND via (20.706,65.619). The nearest In2 GND fill is 3.088 mm away. |
| D-R19-03 TP121 removed | confirmed | No ACT_GATE copper remains west of x 11.14. Q121.4 → R119.1 → via is one clean bend, with no dangling end. |
| D-R19-04 C123 copper | confirmed | ACT_EN runs 1.10 mm straight. The GND run is 0.567 mm plus a 1.075 mm diagonal to the via. Both enter at pad centres. |
| D-R19-05 U1.19 | confirmed | The 1.693 mm² fragment is gone, and DRC reports no library mismatch. The same pattern remains at U1.74 (R20-RTE-02). |
| D-R19-09 second vias | partly | • All vias sit at track nodes, each in its own In2 fill, with holes ≥ 0.45 mm apart.<br>• One clearance figure is stale (R20-RTE-07).<br>• The VLOGIC pair is untidy (R20-RTE-04). |
| D-R19-14 routing | partly | **Clean:**<br>• The AUX pair is F.Cu only and octilinear.<br>• Every reference sample under the AUX pair has In1 GND, except at its own pads.<br>• The R90 run no longer doubles back.<br>• The worst GND-via distance in the north-west corner pours improves from 6.95 to 5.18 mm.<br>**Findings:**<br>• The GPS pair is 1.66 mm shorter but takes two jogs per trace (R20-RTE-03).<br>• The TP82 stub is 4.03 mm (R20-RTE-01).<br>• The ESD clamps are 6.2 mm from the pins (R20-RTE-05). |

## Findings

- **R20-RTE-01 (new): TP82 stub.** Moving TP82 to B(11.0,17.6) makes its dead-end USB_LIMITED stub 4.03 mm long with
  two bends (it was 1.0 mm).
  - **Alternative:** B(11.2,20.7), checked legal. It sits on the extension of the existing diagonal, so the stub
    shrinks to 0.85 mm with no new bend.
  - **Margins at the alternative:** 1.075 mm to foreign copper (against 1.0 mm) and 1.855 mm M-6. No courtyard overlap.
- **R20-RTE-02 (new, missed): U1.74 fragment.** A via-less 0.282 mm² F.Cu GND fragment hangs on U1.74's pin tip, at
  x 17.10–17.90, y 34.20–34.76. It is the same class as R19-RTE-01. The fix is the same one-line pad override.
- **R20-RTE-03 (new): GPS pair jogs.** The GPS pair (PD8 / PD9) takes two 45° jogs per trace.
  - **Cause:** C90's fan-out vias sit at (26.425, 30.5 / 32.1), east of the C90 pads, and RADIO_TX's diagonal limits
    the space beyond them. With both in place, a single diagonal per trace has no room.
  - **Alternative (Inference):** with the C90 vias moved to the west side, each trace needs only one diagonal, with
    0.154 mm clearance.
- **R20-RTE-04 (new): VLOGIC via pair.** The pair forms a 2.6 mm loop:
  - The first via sits 0.42 mm off both runs, on doglegs.
  - The second via hangs on a 0.85 mm diagonal.

  An in-line pair on the straight run y 81.75 is possible (Inference).
- **R20-RTE-05 (new): J440 clamp distance.** J440's ESD clamps are 6.2 mm from its pins; J410 / J420's are
  3.1–3.4 mm. J440's cell is on the top, east of the body; the other ports' cells are on the bottom under the body. This
  is not recorded.
- **R20-RTE-06 (new, missed): C89 under-body via.** The under-body via record (R19-RTE-04) lacks C89.
  - **C89:** R167.2's GND via sits 0.186 mm from the BAT_IN pad, under the 1206 body. The via is tented.
  - **Also found:** five 1210 capacitors with a via 0.40–0.75 mm from their pads.
- **R20-RTE-07 (new): stale records.**
  - Section 6 still carries `a3144b15` inventory figures.
  - The D-R19-09 clearance figure for (26.45,11.95) should be 0.929 mm (to the AUX feed), not 2.000 mm.
  - D-R19-01's "no new neck < 0.5 mm" is true, but it leaves out the new In2 GND_CH1 finger (0.60 mm neck, 0.126 mm²
    detached at a 0.6 mm opening).
- **Carried, with copper unchanged or refreshed:**
  - **R20-RTE-08 (R19-RTE-05):** layer-change returns over the In2 rails.
  - **R20-RTE-09 (R19-RTE-06):** detours. 116 non-pour nets, 1504.3 mm routed against a 1239.9 mm octilinear spanning
    tree, 1.213×.
  - **R20-RTE-10 (R19-RTE-07):** the USB pair.
  - **R20-RTE-11 (R19-RTE-08):** copper under U4.

## AVA comparison

- **Tidier than `a3144b15`:**
  - ACT_GATE is 7.1 mm shorter, with no probe arm.
  - The U1.19 debris is gone.
  - The GPS pair is shorter.
  - The R90 run is direct.
  - The AUX cell is a compact, straight-wired column.
- **Less AVA-like:**
  - TP82 sits on a long stub, where AVA probes at part pads.
  - The GPS escape double-jogs.
  - The VLOGIC via pair has doglegs.
  - J440's clamps are far from its connector.

## Fix now

Both CAD items below are low-risk generator edits. Bundle them with any CAD reopening; on their own they are
cleanliness only and would restart the clean pair.

1. **U1 pad 74:** set its zone connection to `ZONE_CONNECTION_NONE` in `r10_pcb.py`, as for pad 19.
2. **TP82:** move it to B(11.2,20.7), and let one USB_LIMITED segment (15.55,25.05)-(11.2,20.7) replace the three that
   reach it now.

The records parts of R20-RTE-03, -05, -06 and -07 can be fixed now without touching the board.

## Limits

- This review covers CAD geometry only. Not done: field solve, ESD or signal-integrity simulation, neck current
  analysis, and any physical test.
- The alternatives in R20-RTE-03, -04 and -05 are Inference. They were not DRC-checked on a modified copy.
- The full `tools/check.sh` and its self-tests were not run.
