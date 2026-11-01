# Round 21 power review (Claude)

Target commit `accfff4947266a23cf60a63f3d92be047f5391b5`. PCB SHA-256 `0dc847761de94a45cf68b1c82ec91f38e9d4ebb7297abc7108e3df9a454940d3`, the same before and after the review.
**Result: 0 Critical / 0 Major / 2 Minor (all new).** Evidence: [round21_power.json](round21_power.json).

Scope: battery entry to every rail, the round 20 polish changes first (D-R20-02 FB tap, D-R20-11 C87 text, D-R20-08 tab keep-out, D-R20-05 rings), then U9 / R166 / C88 / C84, VLOGIC, 3V3, PORT_5V3, PORT_4V8 with the AUX feed, RAW_ACT and the R134 fire path, and the D-R19-09 second vias.

## Findings

**R21-PWR-01 (Minor): Two regulator feedback pins still hang on one via each; K-power single_via_opens covers only R402.1.**
- U2 (AP63203WU-7, the 3V3 buck, fixed 3.3 V) pin 1 FB at B(24.05,68.6) joins 3V3 only through the B.Cu 0.4 mm run (24.05,68.6)-(23.2,68.6) and the via (23.2,68.6) to In2 3V3. No B.Cu 3V3 pour exists. Seeded copy with that via removed: kicad-cli 10.0.7 DRC reports 1 unconnected item (U2.1 track vs via (23.0,70.0)).
- U401 (TPS7A9101, port LDO) pin 3 FB at B(28.75,13.6) joins its divider R402.2 / R403.1 (both on F.Cu, F(32.225,12.6) / F(32.225,14.4)) only through the via (29.75,13.6). Seeded copy with that via removed: DRC 1 unconnected (B.Cu run (28.75,13.6)-(29.75,13.6) vs F.Cu run (29.75,13.6)-(32.225,13.6)).
- tools/check_r10.py SINGLE_OPEN_TAPS (line ~2413) lists only (PORT_4V8, R402.1); neither pin above is checked, and K-power passes on the board.
- Control-pin survey of the other power ICs: U400 FB (PORT_FB / PORT_FB_TOP) all F.Cu, no via; U9 OVLO / ILIM / dV/dt, U11 OVLO / ILIM / SS, U402 ILIM all local B.Cu, no via; U10 ILIM via (14.825,26.0) single but an open ILIM lowers the TPS2553 limit (larger RILIM gives a lower limit, SLVS841G p7 RILIM table), fail-safe.
- Source: AP63203: FB is the output-sense pin, fixed 3.30 V (3.27-3.33 V) internal divider (https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf DS41326 Rev 3-2 p2 pin table, p5 VFB); block diagram p3 shows an FB UVP comparator at 0.6 V; p10 names overvoltage protection without describing its sensing.
- Source: TPS7A91: FB leakage -100..+100 nA (https://www.ti.com/lit/ds/symlink/tps7a91.pdf SBVS282A p5); no open-FB behaviour stated.
- Source: STM32H743: VDD absolute maximum 4.0 V (https://www.st.com/resource/en/datasheet/stm32h743vi.pdf DS12110 Rev 8 p106).

Impact: Inference (not stated by the makers): with U2.1 open, the fixed AP63203 regulates its internal divider node, which sits at GND, so the converter runs to maximum duty and 3V3 rises toward VLOGIC (up to about 8.4 V, current-limited at 2.5-3.1 A), above the MCU 4.0 V maximum and the sensors; if the undocumented UVP / OVP stops it instead, 3V3 is lost. Either way the primary computer is lost (recovery falls to the isolated Blue Jay); a pyro output needs both PC1 and PE4 driven high, so a fire from a damaged MCU is not demonstrated. With U401.3 open, FB floats on its +/-100 nA leakage: PORT_4V8 is undefined between 0 V and dropout (about 5.2-5.55 V on all three ports, R20-PWR-02's consequence). A manufacturing open is caught by first-article rail checks; a later barrel crack (vibration, thermal cycling) is not.

Fix: Next board change: (1) a second 3V3 via in line on U2.1's run, e.g. extend the B.Cu run west to a via at (22.55,68.6) (scanned legal: 0.187 mm to foreign F/B copper, 0.35 mm hole gap to (23.2,68.6), inside In2 3V3; run route_check / DRC); (2) a second FB link for U401.3: no in-line legal spot exists on y 13.6 east of the via (scanned), and spots near (29.75,14.15) need a parallel loop; preferably move R402 / R403 to B.Cu beside U401 so the divider and FB need no via. Gate: add (3V3, U2.1, L1.2 / C8.1) and (PORT_LDO_FB, U401.3, R402.2 / R403.1) to SINGLE_OPEN_TAPS. Now: name both in the respin list and keep the first-article 3V3 and PORT_4V8 level checks.

**R21-PWR-02 (Minor): D-R20-05 left J1.2 and J400.2 holes 0.250 mm from inner copper, under JLC's 0.3 mm for PTH pads.**
- J1.2 (GND, drill 1.30 mm) at (7.4,77.6): hole wall to In2 RAW_PROTECTED 0.250 mm (round 19 board 50a39de5: 0.550 mm).
- J400.2 (BAT_SW_RETURN) at (7.4,67.6): hole wall to In1 GND 0.250 mm (was 0.550 mm).
- Every other PTH pad (29 of 31, J3 shell included): >= 0.550 mm on In1 and In2 (probe pthinner.py, both boards).
- m3.kicad_dru sets hole_clearance 0.25 mm for everything, so DRC (0 violations) cannot see it.
- Source: https://jlcpcb.com/capabilities/pcb-capabilities "Traces" table: "Inner layer PTH pad hole to copper clearance 0.3mm" (vias: 0.2 mm); through-hole finished size tolerance +0.13 / -0.08 mm.

Impact: Below the fab's published capability by 0.05 mm, with the drill oversize taking a further ~0.065 mm of radius (Inference). A J1.2 to In2 RAW_PROTECTED short shorts U9's output: U9 limits and trips, the board does not power (fail-safe, but a lost board or a CAM query / silent CAM edit). A J400.2 to In1 GND short holds EN low (fail-safe, as D-R20-05 notes). J121.1 and every via are unaffected.

Fix: Add to m3.kicad_dru: (rule "PTH pad hole to inner copper (JLC 0.3 mm)" (layer inner) (condition "A.Type == 'Pad' && A.Pad_Type == 'Through-hole'") (constraint hole_clearance (min 0.3mm))) and refill; or restore 0.55 mm with fill-only In2 / In1 rule areas around J1.2 / J400.2. Re-run K-plane, S-8 and DRC; the extra 0.05 mm pull-back touches one hole on each plane.

## Fix verification

| Decision | Verdict | Measured |
|---|---|---|
| D-R20-02 | confirmed | DRC on seeded copies: opening (29.75,12.6), (29.75,9.95), (30.575,11.6) or (30.5,9.95) alone: 0 unconnected each; opening both OUT vias: 1 unconnected (U401 cut off from the ports, a double fault). DC solve (tools/dc_solve.py, grid 0.1 mm): U401 to R402.1 2.23 mOhm intact, 7.12 / 2.28 / 3.00 / 2.23 mOhm with each via open; port voltages by superposition at 0.20 / 0.26 / 0.10 A (GPS / radio / AUX) stay 4.788-4.794 V for a 4.792 V tap in every case (J440 -8.5..-9.1 mV at 0.3 A alone). The via is 0.25 mm from GPS_RX_MCU; K-power single_via_opens passes on the copy. |
| D-R20-11 | confirmed | Recomputed over C 0.72-1.27 x 220 nF, 1 % R80+R165 / R81, TPS25947 thresholds 1.183-1.223 V rising / 1.076-1.116 V falling and +/-0.1 uA (https://www.ti.com/lit/ds/symlink/tps25947.pdf SLVSFC9C p9): 10.65 / 20.47 / 26.41 ms; 8.50 ms at 5.73 V; 6.58 ms at 5.5 V; 10 ms needs 5.917 V; turn-on 30.3-128.6 ms over 6.0-8.4 V (153 ms at 5.73 V, 189 ms at 5.5 V). Schematic note, sch_check obligation and binding note carry the new figures. |
| D-R20-08 | confirmed | In2 copper in x -0.5..3.0, y 12.5..17.5: none (F, In1, B GND 12.498 mm2 each). 3V3 In2 one piece 1434.20 mm2 (1446.71 before); K-plane necks 0.549 / 0.549 / 0.589 / 0.706 mm, none at the tab; the 3V3 strip between the keep-out and J440's antipads is about 3.2 mm wide (0.2 mm raster). East tabs unchanged (RAW 7.497 + PORT_5V3 3.077 mm2 aft, RAW 12.244 mm2 forward): owner decision, not filed. |
| D-R20-05 (power side) | partly | Confirmed as recorded, but the two 0.250 mm hole-to-inner-copper figures (J1.2 In2, J400.2 In1) are below JLC's 0.3 mm for PTH pads (R21-PWR-02). |
| D-R20-01 | confirmed | BAT_ENABLE vias (19.675,66.6), (21.3,68.9), (17.1,82.8) unchanged; not re-litigated (recorded respin item). |
| D-R19-09 | confirmed | Nine seeded DRCs: each single via of C84 (29.5,82.05)/(29.8,81.15), U402 IN (42.0,61.8)/(42.75,61.8), U401 IN (25.9,8.6)/(26.45,11.95), U401 EN (25.65,14.9)/(24.9,14.9): 0 unconnected. U11.2 (24.3,66.0) removed: 2 unconnected (carried single via, recorded). Copper of these nets unchanged against 50a39de5 (diff). |
| D-R19-14 (AUX feed) | confirmed | U401 to J440.1 29.90 mOhm (9.0 mV at 0.3 A; IPC-2152 neck 0.76 mm In2, 0.4 C); 31.75 mOhm with (29.75,9.95) open, 30.42 mOhm with (30.5,9.95) open; DRC 0 unconnected for each. |

## Fix now

- R21-PWR-02: Add the m3.kicad_dru rule (layer inner) hole_clearance >= 0.3 mm for through-hole pads (exact text in the finding), refill, re-run check.sh; expected effect: J1.2 In2 and J400.2 In1 0.250 -> 0.300 mm, nothing else moves (every other PTH is >= 0.55 mm).
- R21-PWR-01 (part): Optional now, if the CAD lane takes a copper change: second 3V3 via for U2.1 at (22.55,68.6) on a westward extension of the existing B.Cu run, and the U2.1 SINGLE_OPEN_TAPS entry. The U401.3 half needs a re-layout (next board change).

## Closed without a finding

- PORT_4V8 regulation with a single via open: within 4 mV (above): closed.
- Copper diff 50a39de5 -> 0dc84776: power nets change only by the PORT_4V8 via + 0.4 mm stub, the USB_LIMITED TP82 spur (0.4 mm, a dead-end test spur) and the In2 fills (3V3 -12.5 mm2 at the tab, RAW_PROTECTED +1.98 mm2 at J1.2). U9, R166, C88, C84, VLOGIC, RAW_ACT, R134, PYRO1_IGN / OUT copper unchanged: hot-plug and hold-up inputs unchanged.
- Fire path: RAW_ACT Q121 -> R134.2 5.24 mOhm, PYRO1_IGN R134.1 -> J121.2 9.23 mOhm (0.5 mm B.Cu, no vias); a 20 ms 1.3-1.5 A pulse is not an IPC-2152 continuous case.
- BAT_IN J1.1 -> U9.5: 16.71 mOhm, 48 mV at 2.9 A, one 1.0 / 0.5 mm via carrying 2.9 A, neck 1.00 mm F.Cu at 19.2 C (IPC-2152, no plane credit) at the 2.9 A design current: unchanged, gated by K-power.
- PORT_5V3: L400.2 -> U401 IN 6.08 mOhm (largest via 0.45 A at 0.6 A); -> U402.1 35.93 mOhm, 45 mV at 1.25 A, largest via 0.90 A, In2 neck 1.02 mm at 4.1 C.
- J1.2 thermal relief (pad override) on F / In1 / B: about 12 spokes of 0.3 mm for a <= ~3 A return, low loss; unchanged since round 19.
- U10 USB_ILIM single via: open ILIM lowers the TPS2553 limit, USB-only bench path; fail-safe.
- A short on one port harness kills all three PORT_4V8 ports: recorded (M3_R10 Power, ORDERING 8.3 port-short test).
- RAW_PROTECTED: U9.6 -> U11.2 7.05 mOhm (9.2 mV at 1.3 A; the carried single via (24.3,66.0) carries all 1.30 A); U9.6 -> U400.2/3 37.77 mOhm (60 mV at 1.6 A), B.Cu neck 1.05 mm at 5.6 C; U9 OUT via (20.3,79.1) carries 0.92-1.13 A of the two (unequal share, both 0.5 / 0.3 mm, within the gated pair): unchanged, closed.
- 3V3: L1.2 -> U1 VDD pins 7.33 mOhm (5.9 mV at 0.8 A; 42 % F.Cu through the bridge via (26.4,79.26), 58 % In2); the narrowest cut (0.29 mm, 6.1 C at 0.8 A) is the MCU pin fan-out at the 4 % level, and the K-plane 0.549 mm In2 necks near U2 do not limit: closed.

## Executed

- Board SHA-256 before and after (canonical file): 0dc84776... both; the probe copy (git archive of accfff4) matches.
- kicad-cli 10.0.7 DRC on the copy: 0 violations, 0 unconnected, 0 parity.
- 17 seeded via-removal DRCs on copies (PORT_4V8 x4 + both OUT vias, PORT_LDO_FB, U2.1 3V3, USB_ILIM, C84 x2, U402 x2, U401 IN x2, U401 EN x2, U11.2).
- 35 dc_solve.py runs on PORT_4V8 (5 board states x 7 pairs) and superposition of port voltages; 9 rail solves with --necks (BAT_IN, RAW_ACT, PYRO1_IGN, PORT_5V3 x2, PORT_4V8 J440, 3V3 and RAW_PROTECTED where they finished: see coverage).
- check_r10.py --only K-power,K-plane,K-region on the copy: OK.
- Via-to-plane contact map of every power via; GND / power pad zone-connection modes; PTH hole to inner foreign copper on both boards; copper under the three tab windows; In2 raster of the west aft tab.
- Legal-spot scans (0.025 mm grid) for second vias at U2.1 and U401.3.
- C87 / EN timing recalculation (c87.py).
- Datasheet reads (cached maker PDFs): DS41326 Rev 3-2, SBVS282A, SLVSFC9C, SLVS841G (TPS2553), DS12110 Rev 8; JLC capabilities page (live).

Probe files: `.supervisor/r21_power/`.

## Limits

- No thermal simulation or measurement; the AUX allowance stays provisional as recorded.
- Hot-plug and hold-up models not rerun (their copper and parts are unchanged).
- DC solves: room-temperature copper, 20 um via plating; port loads are allocations.
- Open-FB behaviour of AP63203 / TPS7A91 is Inference: neither maker states it.
- Legal-spot scans check F/B copper (pours ignored), holes and In2 fill only; route_check not run on a candidate.
- The 3V3 / RAW_PROTECTED solves took about 6-7 min each at 0.1 mm; no grid-refinement check was run on them.
