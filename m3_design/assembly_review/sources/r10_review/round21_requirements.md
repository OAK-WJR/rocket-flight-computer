# Round 21 - requirements and physics roots (Claude)

Target commit accfff4; board SHA-256 0dc84776... unchanged before and after.

**Totals: 0 Critical / 0 Major / 6 Minor.** Every REQUIREMENTS row and the owner decisions (single switch, OQ-1..7, D-R19-14 AUX port, D-R20 polish) trace to the board. The connector poses, pin nets, gate networks (AGENTS 2.4), removed hardware, supports and outline all match. pin_table r10_net matches the board on 100 / 100 pins. DRC (all severities, with parity) is 0 and route_check r10 is 0 failing. The findings are stale text, one gate-scope gap and one flight-envelope root.

## Findings

- **R21-REQ-01 (Minor, new): stale schematic notes.** The sensors sheet still says "U4 = LSM6DSV320X ... +/-32..320 g ... DS14623", but the fitted part is the ISM6HG256X, whose high-g range tops out at +/-256 g (DS15034 p1). The pins 10/11 pull-up / OIS_PU_DIS obligation does hold for the ISM (DS15034 Table 25 p52). The diagnostics note cites a camera-regulator "U8" USB self-test: there is no U8, and the camera rail is off on USB power. Fix: generator text.
- **R21-REQ-02 (Minor, new): fuse note contradicts OQ-6.** The battery_entry note "Input supply must be fused/current-limited externally" contradicts the owner's no-battery-lead-fuse decision, which is in Accepted risks and the Battery harness row. Fix: restate the note as the OQ-6 residual.
- **R21-REQ-03 (Minor, new): Camera row omits J440.** The REQUIREMENTS Camera row names only J410 / J420 as self-powered back-feed ports. J440.1 is the same PORT_4V8 net. AGENTS, ORDERING 599 and FMEA already include AUX.
- **R21-REQ-04 (Minor, new): arming chain is unclassified.** BAT_SW_SOURCE / BAT_SW_RETURN / BAT_ENABLE are class "other" in route_check R10_CLASSES, although J400 is the arming device (F8, AGENTS 2.1) and M2 makes arming nets critical. Effects:
  - The BAT_ENABLE tiny jog at B.Cu (21.0, 68.6) (mid 0.424 mm) is only a noncritical leftover.
  - The 2.973 mm short layer hop at (19.675, 66.6) is information only.
  - Its vias are 1.42 / 1.87 / 2.90 mm from the nearest GND via. The partner-via rule has no physical root on this 50 ms node and would be AUD-2-exempt.

  Fix: classify the nets (pyro plus AUD-2 slow list) or record the reason.
- **R21-REQ-05 (Minor, new): flight envelope out of date.** The flight-2 figures (3.4-3.6 km, 460-525 s, 28-37 g) predate the Mach 1.9 design point. A drag-free coast from about 650 m/s is 21.5 km, so a 3.6 km apogee is implausible (Inference). Flight 1 (K850DM) still has no envelope. Board impact found: none. A 6 km / 800 s flight logs about 3 MB against 16 MB of QSPI. F3's 10 km requirement then has a physical root and is not spare margin. Fix: re-derive the envelope from the OpenRocket model, then re-check the 525 s in the Temperature row, Q_flight and the F5 windows.
- **R21-REQ-06 (Minor, carried R19-REQ-08, partly fixed): R7-R9 text in current rows.** M2 keeps the R8 D10 / U31 / RF-module and R7-R9 pour-list clauses. The Board position row keeps the R9 coax-loop allocation (jack 9.5 mm + plug + RG316). Fix: move them to HISTORY section 3.

## Fix verification

| Change | Verdict | Measured |
|---|---|---|
| D-R19-14 | Confirmed (one stale row, R21-REQ-03) | J440 cell identical to J410 / J420; ports on USART3 / UART5 / USART6 at pins 55/56, 51/52, 63/64; legends and sheet notes updated |
| D-R19-10 / D-R20-11 | Confirmed | Recomputed tau 50 ms, turn-on 87.6 ms and drop-out 18.9 ms at 6.0 V; worst-case figures consistent across docs and the sheet; no stale strings |
| D-R19-11 | Partly | Part fitted; schematic text stale (R21-REQ-01) |
| D-R19-04 | Confirmed | 0.218 V gate against the PC1 pull-up |
| D-R20-01 | Not done, as recorded | Three EN vias; 27.9 mm of track on the net |
| D-R20-02 | Confirmed (presence only) | Via (30.575, 11.6) present |
| D-R20-03 | Confirmed | U1.74 has no pour connection |
| D-R20-04 | Confirmed | TP82 at B(11.2, 20.7) |
| D-R20-05 | Confirmed | Unconnected-layer mode 3 on J121.1 / J400.2 / J1.2; J121.2 keeps its rings |
| D-R20-08 | Confirmed (presence only) | Rule area present |
| D-R20-09 | Confirmed | Clamp positions as claimed; vias swapped |
| R19-REQ-03 / -04 / -05 | Confirmed | |
| R19-REQ-08 | Partly | R21-REQ-06 |

## Fix now

- R21-REQ-01 and -02: three schematic-note rewrites in r10_sch.py. Text only; netlist and PCB hash unchanged.
- R21-REQ-03: add J440 to the Camera row.

## Closed candidates

- **AUX 100 mA limit as an oversized margin.** The radio's 300 mA allocation covers the LR900-F's 1 W maximum average draw: 222 mA at 4.5 V (maker manual).
- **AGENTS 2.2 and the BAT_IN feed to Q120 / Q121.** The pyro bus is still taken after the load switch; the owner accepted the single-switch residual.
- **Gate networks.** All three gate networks are complete.
- **Continuity bias.** At most 0.33 mA flows through the e-match.

Open owner decisions (cost, P3 factor, hold-up, pad-energy basis, east tabs, U4 stock) and the parent VEHICLE.md row are noted, not filed.

## Coverage limits

- CAD and document lens only: no bench, firmware or flight data.
- R21-REQ-05's apogee is an Inference; no trajectory simulation was run.
- check.sh was not run on the canonical tree. DRC and route_check outputs are in the probe directory.
