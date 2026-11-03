# Round 23: return paths and EMI (Claude, routing lens)

**0 Critical / 0 Major / 1 Minor (1 new).**
- Target commit `c70d261`.
- PCB `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1`, the same before and after the review.
- Full data: [round23_routing.json](round23_routing.json).
- Probe scripts, rasters and renders: `.supervisor/r23_routing/`.

## Angle

This round looks at return paths and EMI over the whole board, not at the M2 checklist:
- trace each fast net's reference layer by layer;
- the fire loop;
- servo-to-sensor coupling;
- the In2 islands under the port buck and the LDO.

## Gate results on this board (probe copies)

- **DRC** (kicad-cli 10.0.7, all severities): 0 violations, 0 unconnected.
- **route_check `--profile r10`:** 0 failing, 6 unrecorded leftovers, as recorded.

## Return paths

**Reference planes.**
- In1 is one solid GND piece, broken only by antipads.
- Every In2 zone is one piece.
- Every 0.1 mm sample of every fast or critical track lies over reference copper, except inside its own via antipad. The trace edge is always 0.0–0.1 mm or more inside that copper. Nets covered:
  - QSPI, SPI3 microSD, IMU SPI, USB and HSE;
  - the GPS, radio, AUX and camera UARTs;
  - the servo lines.
- No fast net crosses a plane split or slot. There are no via fences (no RF on the board).

**References by layer.**
- F.Cu runs over In1 GND.
- B.Cu runs over one In2 net per run:
  - SD_* over 3V3 for 30.0–30.8 mm each;
  - HSE over the Y1 GND island (37.2 mm², 8 vias);
  - the GPS and radio wire nets over PORT_4V8;
  - camera and AUX over 3V3;
  - the servo outputs over RAW_PROTECTED.

**Layer changes.** These are carried (R19-RTE-05, owner row 8: 21 of 25 over an In2 rail) and confirmed. The new figure is the nearest capacitor between GND and the B.Cu-side rail at each via:

| Nets | Nearest capacitor (mm) |
|---|---|
| QSPI | 1.25–2.72 (QSPI_NCS 5.40) |
| SD (SCK, MISO, MOSI, CS) | 4.61–6.10, all to C17 |
| SPI1 | 4.96–5.63 |
| IMU_CS | 5.27 |
| GPS / radio | 3.19–6.40 |

Each via has a GND partner via 0.77–1.44 mm away. This is not re-filed.

## Fire loop

**Path.** BAT_IN → Q120 → Q121 → RAW_ACT → R134 → J121.2 → e-match → J121.1 → Q124 → GND → J1.2.

**Area.** 85.7–90.0 mm² absolute, in two lobes. The net area (dipole) is 18 to −28 mm², depending on the return path assumed.

**Distance to sensitive parts:**

| Part | Nearest fire copper (mm) | Field (µT per A) |
|---|---|---|
| IMU U4 | 8.81 | 1.6 |
| Crystal Y1 | 10.52 | 0.81 |
| Barometer U5 | 2.93 (opposite side, over In1 GND) | 7.2 |

**Assessment.**
- At the 1.279 A worst case the field is at most 9.2 µT, and neither the IMU nor the barometer has a magnetometer.
- Q124 switches slowly: its gate network (R126 220 Ω with C126 220 nF) has a time constant of 48 µs (Inference). Crystal-loop EMF is about 0.2 µV.
- Not filed.

## Servo coupling

- No servo copper is within 8 mm (in plan, on any layer) of an IMU or barometer net. The nearest clock line is HSE_OUT, 4.3 mm away.
- The reference changes from 3V3 to RAW at the 1 kΩ resistors (R150–R153). The resistors limit the return current to 3.3 mA.
- D121's GND leg is a 0.95 mm track to a via. Semtech's SRV05-4 datasheet, p.4, needs no bypass on pin 5.
- Not filed.

## In2 islands under U400, L400 and U401

- **U400** sits over RAW, its own input.
- **L400** straddles the RAW / PORT_5V3 gap, shielded by In1 GND 0.203 mm below the top layer.
- **U401** straddles the PORT_5V3 / PORT_4V8 boundary.
- **Forward RAW feed.** It reaches U400 only through the east-edge strip, x 44.0–45.5: 1.5 mm wide and about 58 mm long. Calculation: about 22 mΩ, or about 29 mV at 1.3 A. This is planned in D-R2-03 / -05 and tab row 28.
- **Necks:**
  - PORT_5V3: 1.12 mm local neck at U402's vias;
  - PORT_4V8: at least 1.31 mm;
  - 3V3 finger: 0.40–0.55 mm, as recorded.
- **Hot loops:**
  - U400 with C401: about 7.6 mm², over In1 GND;
  - U2 with C6: about 4 mm².
- Not filed.

## Finding

**R23-ROUTING-01 (Minor, new): R10 has no GNSS self-interference check.**

**The problem.**
- Y1 runs at 25 MHz. 25 MHz × 63 = 1575.000 MHz, 0.42 MHz from GPS L1 (1575.42 MHz). That is inside the C/A main lobe, ±1.023 MHz (IS-GPS-200 §3.3.1.1 and §3.2.1.3).
- The M10 GPS (F10) hangs on J410's harness, which carries PORT_4V8, GND and the UART lines.
- R9's ORDERING §5 (line 167) recorded this harmonic and prescribed C/N0 and MON-SPAN checks.
- R10's §8.3 inherits only §5's static, leakage, reset, bootloader, power-transition, thermal and sensor tests (line 572). No R10 document has a GNSS check.

**Impact.** The spur level is unknown (Inference). A spur could cost tracking data, but it affects no flight-control or pyro function.

**Fix (text only).**
1. ORDERING 8.3: log UBX-NAV-SIG C/N0 and UBX-MON-SPAN with the GPS on its flight harness in the bay, in two conditions:
   - the board unpowered and the GPS on a bench supply;
   - the board at its flight clock, writing QSPI and SD, with the camera on and the servos stepping.
2. M3_R10 firmware note: avoid SPI3, QSPI and timer clocks that have a harmonic within ±1.023 MHz of L1, such as 25 or 75 MHz. Label this an Inference.

## Fix verification

| Change | Verdict | Evidence |
|---|---|---|
| D-R22 (all) | confirmed | Same PCB hash. Gerber and drill layer contents are identical; only the job file differs. route_check, the DRU, the project file and check.sh are unchanged. The check_r10 changes only add checks. |
| D-R22-04 (R22-ROUTING-01) | confirmed | The table's added rows and R89's via are present. |
| D-R22-07 | confirmed | Clamp GND legs are 0.70 / 0.80 mm. |
| D-R21-01 | confirmed | Hole walls are 0.550 mm from foreign inner copper. No fill splits. |
| D-R21-02 | confirmed | The 0.4 mm B.Cu segment is present. |
| D-R21-04 | confirmed | The BAT_ENABLE hop is exact. |
| D-R21-05 | confirmed | R81 and C87 poses are as recorded and both vias are gone. |
| D-R21-06 / D-R20-08 | confirmed | Band areas are 7.50, 3.08 and 12.24 mm². The west aft band is empty. |
| D-R21-07 | confirmed | Clamp path lengths are 3.975–4.388 mm. |

## Not filed (details in the JSON)

- **Edge stitching.** The perimeter gap is 50 mm on the east edge. But the port GND pins and vias at x 36–38.6 stitch the pours at about 16 mm pitch. The worst point is 12.2 mm from a stitch, and the half-wave resonance is above L1.
- **HSE_OUT and NRST.** They run in parallel for 5.74 mm at 0.30 mm (about 0.3 pF).
- **The USB_LIMITED In2 slot.** Only slow nets cross it (recorded).
- **Ground shift from servo and camera return current.** About 0.1 mV.

## AVA comparison

- The records claim In1 solid GND, a local In2 GND under the crystal and continuous fast references (AVA section 6 items 5 and 9). All three hold on the board.
- AVA's images show no inner layers, so its return-plane practice cannot be compared further.

## Comparison with round 22 (read after writing the above)

- Round 22 took the M2 angle. Its only finding, R22-ROUTING-01, is fixed and confirmed here.
- R23-ROUTING-01 is new.
- Both rounds agree on 21 of 25 critical vias over an In2 rail, and on the D-R21 fixes.

## Fix now

R23-ROUTING-01: text only, with no board or check change.

## Limits

- Geometry and first-order calculation only. There is no field solve and no SI, EMI or ESD simulation or measurement.
- The full `tools/check.sh` was not run.
- IS-GPS-200 page numbers were not checked.
