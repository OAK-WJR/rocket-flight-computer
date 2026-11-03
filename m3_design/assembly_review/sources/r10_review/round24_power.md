# Round 24 power lens (Claude)

Target `f2b8251`, board `1407e8506efbac0f664b3aeb65568c32ae9670c9b45b502a465cba1130de522e` (verified before and after). Totals: **0 Critical, 0 Major, 2 Minor.**

## Findings

### R24-POWER-01 (calc, Minor): D402's leakage is said to leave the EN timing figures unchanged, but with the record's own 50 nA bound the worst-case drop-out, pack floor, chatter limit and turn-on figures all move

- **Contradicts:** D-R24-11 ('That is the same as 25 nA at the EN node, a quarter of the 0.1 uA EN leakage D-R20-11's timing already carries. The EN timing figures are kept'); docs/M3_R10.md 'Logic and switch' ('so the EN figures below stand') and 'J400 ESD' ('the EN timing figures are kept'); docs/ORDERING.md 8.3 'J400 ESD' and docs/REQUIREMENTS.md F9 ('so the EN timing figures stand'). The figures themselves are D-R20-11's worst case with +-0.1 uA EN leakage: drop-out 10.6 / 20.5 / 26.4 ms at 6.0 / 7.4 / 8.4 V, 8.5 ms at 5.73 V, 6.6 ms at 5.5 V, pack >= 5.92 V for 10 ms, turn-on 30-129 ms (M3_R10, REQUIREMENTS F6 and F4's '>= 5.92 V under four stalls' option, ORDERING 8.3), and the chatter limit 'above about 21-25 %' against the '< 20 %' pass rule (ORDERING 8.3, REQUIREMENTS F6). Basis: TI SLVSFC9C p9 (VUVLO(R) 1.183/1.20/1.223 V, VUVLO(F) 1.076/1.09/1.116 V, IENLKG +-0.1 uA); Infineon ESD103-B1-02 Rev 1.3 Table 3 p5 (IR <= 50 nA at VR = 15 V, 25 C).
- **Evidence:** D402 (ESD103-B1-02EL) B(4.45,65.9) from J400.2 (BAT_SW_RETURN) to GND; R80 / R165 470 kOhm 1 %, R81 300 kOhm 1 %, C87 220 nF (-28 % / +27 % as D-R20-11). Calculation. D-R20-11's corner model (resistors +-1 %, C87 0.72 / 1.27, both threshold extremes, EN leakage +-0.1 uA) reproduces every published figure exactly without D402 (10.651 / 20.473 / 26.414 ms, 8.496 ms at 5.73 V, 6.579 ms at 5.5 V, pack floor 5.917 V, turn-on 30.31-128.56 ms, chatter trip 20.6 % at 5.73 V). D402 is then added as a 0-50 nA sink at J400.2: with J400 closed it acts through R80 (D-R24-11's own 25 nA equivalent at EN); with J400 open J400.2 is joined only to R165 and D402, so the same diode sinks EN directly through R165, a path the record does not consider. With D402 at its 50 nA bound: worst drop-out 10.345 ms at 6.0 V (10.465 ms counting only the closed-switch effect D-R24-11 quantified), 20.11 / 26.02 ms at 7.4 / 8.4 V, 8.20 ms at 5.73 V, 6.30 ms at 5.5 V; the 10 ms criterion needs a pack of at least 5.956 V (5.941 V closed-only) instead of 5.917 V; turn-on up to 130.27 ms (was 128.56); the worst-corner chatter open fraction that trips U9 at 5.73 V falls from 20.6 % to 20.0 % (20.2 % closed-only), i.e. onto the 20 % pass criterion. The closed-switch EN shift 5.685 mV and J400.2 at 5.216 V (8.4 V) are confirmed. (`m3_design/assembly_review/m3.kicad_pcb; .supervisor/r24_power/en_d402.py -> en_d402.json`)
- **Impact:** The worst-case bounds the bench and flight-2 pack choices rely on are not worst case any more: a flight-2 pack holding 5.92-5.95 V under four stalls meets REQUIREMENTS F4's option as written yet misses the 10 ms immunity at the D402 bound, and the chatter pass rule (< 20 %) no longer has the margin the text states (21-25 %). No safety effect (D402 only pulls EN down).
- **Fix:** Text only: either recompute the D-R20-11 figures with D402's 50 nA bound added (closed: at J400.2; open: at EN through R165) and carry them everywhere they are quoted (10.3 / 20.1 / 26.0 ms, 8.2 ms at 5.73 V, 6.3 ms at 5.5 V, pack >= 5.96 V, turn-on 30-131 ms, chatter trip about 20-24 %, so set the pass rule below 20 %, e.g. < 18 %), or keep the figures and state that they exclude D402, giving the shifts above; replace 'the EN timing figures are kept / stand' in D-R24-11, M3_R10 (two places), ORDERING 8.3 and REQUIREMENTS F9.

### R24-POWER-02 (doc, Minor): The first-article bench-ramp window (turn-off 4.5-4.8 V, turn-on 4.9-5.2 V) excludes healthy boards: the nominal turn-off, 4.505 V, sits on the window's lower edge

- **Contradicts:** docs/ORDERING.md 8.3 'J400 ESD, first article' ('expect turn-off 4.5-4.8 V and turn-on 4.9-5.2 V'), docs/REQUIREMENTS.md F9 and docs/M3_R10.md 'J400 ESD' (same window) against the correct calculation from TI SLVSFC9C p9 (VUVLO(R) 1.183/1.20/1.223 V, VUVLO(F) 1.076/1.09/1.116 V, IENLKG +-0.1 uA) with the fitted 1 % divider R80 / R165 470 kOhm, R81 300 kOhm.
- **Evidence:** U9 TPS259470L B(18.5,81.6) EN/UVLO; divider BAT_IN-R80-J400-R165-EN-R81-GND (ratio 300/1240 = 0.2419). Calculation: pack voltage at the EN threshold = VT x (R80+R165+R81)/R81 + I_EN x (R80+R165) (+ I_D402 x R80), over all resistor (1 %), threshold and leakage corners. Healthy-board range: turn-off 4.288-4.778 V (4.802 V with D402 at 50 nA), nominal 4.505 V; turn-on 4.723-5.227 V (5.251 V with D402), nominal 4.960 V. The documented window cuts 4.29-4.50 V of turn-off and 4.72-4.90 V of turn-on out of the healthy range, and its upper turn-on edge (5.2 V) is below the healthy maximum. (`.supervisor/r24_power/ramp_window.py -> ramp_window.json`)
- **Impact:** The required first-article / post-event check cannot be carried out correctly as written: a healthy board (about half of nominal parts on turn-off) reads outside the window and would be taken for a damaged EN pin, while the window gives no stated basis for the edges it does use.
- **Fix:** Text only, in ORDERING 8.3, REQUIREMENTS F9 and M3_R10: replace the window with the calculated healthy range, turn-off 4.29-4.80 V and turn-on 4.72-5.25 V (TI SLVSFC9C p9, 1 % resistors, +-0.1 uA, D402 <= 50 nA), and say that a reading above the top edge indicates extra EN leakage to GND (outcome (b)) and one below the bottom edge leakage from IN.

## Fix verification

| Change | Measured | Verdict |
|---|---|---|
| D-R24-02 Q120 / Q121 ACT_GATE second barrels | (15.4,72.85) F.Cu T3 / B.Cu T3, B.Cu 0.361 mm to Q120.9 BAT_IN, hole edge 0.618 mm; (11.74,72.3) F.Cu / B.Cu, hole edge 0.549 mm; Q120.4 and Q121.4 to R121.1 / R120.2 / R119.1 joined with any one via open | confirmed |
| D-R24-03 BOOT0 second barrel | (14.2,46.0) F.Cu 0.150 mm to I2C1_SCL, B.Cu 0.211 mm to C31.1, hole edge 0.266 mm; U1.94 -> R5.1 joined with either via open | confirmed |
| D-R24-04 VCAP2 second barrel | (18.3,36.8) B.Cu 0.211 mm to NRST, hole edge 0.283 mm; U1.73 -> C20.1 joined with either via open | confirmed |
| D-R24-05 U9 EN kept | BAT_ENABLE via (17.10,82.80) unchanged; R81 / C87 unchanged; EN timing model reproduces D-R20-11 exactly (without D402) | confirmed |
| D-R24-07 U402 GND second via | (32.3,60.1) on a 0.3 mm B.Cu link, joins F.Cu / In1 / B.Cu GND; B.Cu 0.200 mm to U402.6, F.Cu 0.210 mm to SERVO4_MCU | confirmed |
| D-R24-08 monitor-tap second vias | VLOGIC (34.5,62.4) B.Cu 0.150 mm to PORT_5V3; LOGIC_SOURCE_ST (30.45,51.4) 0.171 mm to GND via (30.15,52.0); 3V3 (28.1,59.4) joins In2 3V3; each tap joined with any one via open | confirmed |
| D-R24-09 U401 divider on B.Cu | R402 B(30.9,12.85), R403 B(30.9,14.6); FB, top and bottom with no via; three vias removed; OUT vias (29.75,11.65) and (29.75,9.95) both on In2 PORT_4V8; T 0.075 mm inside R402.1 land; 4.792 V | confirmed |
| D-R24-10 USB OV / ILIM legs | (16.6,28.0) B.Cu 0.2 mm + In2 0.4 mm links, U10.6 -> R87.1 joined with (16.0,28.0) open; (22.0,62.25) remains single as recorded | confirmed |
| D-R24-11 D402 at J400.2 | B(4.45,65.9) rot 90, tap 4.114 mm from J400.2 own pad, return 0.7 mm to GND via (5.15,65.575) on F / In1 / In2 / B GND; ring 1.79 / 2.127 mm from J400 barrel walls; closed-switch EN shift 5.685 mV; S-5 / K-ports OK. The claim that the EN timing figures are kept is not right (R24-POWER-01) | partly |
| D-R24-14 east RAW_PROTECTED strip unchanged | In2 raster diff: RAW_PROTECTED changes only at x 10-21 and the R92 / TP88 vias (x 32-37, y 86-87); none on the x 44.0-45.7 strip | confirmed |
| D-R24-15 R92 / TP88 moved | RAW_PROTECTED via (30.175,85.9) joins In2 RAW; GND vias (32.65,86.7), (36.6,86.4) join the GND fills | confirmed |
| D-R24-17 U9 trunk, C88, C82 legs, U400 via | C88 B(18.67,83.56) rot 0 on U9.5 axis; 0.3 mm 1.96 mm and 0.7 mm 1.74 mm pieces match POWER_NARROW; IN via (17.5,87.15) on one 1.0 mm diagonal; F.Cu chamfer 1.018 mm; C82.1 legs 0.7 mm to (20.3,79.1) and (21.1,78.25); U400 via (14.1,8.5); hot-plug re-run identical | confirmed |

## Observations (not counted)

- BAT_IN DC solve J1.1 -> U9.5 (tools/dc_solve.py, 0.1 mm grid): 16.71 -> 15.98 mOhm; neck 1.00 mm F.Cu unchanged (19.2 C at 2.9 A, IPC-2152 no plane credit); the single 1.0 / 0.5 mm IN via (17.5,87.15) carries all 2.9 A, as R19-GATE-05 designs.
- U9 IN's 0.3 mm entry is now 1.96 mm long, 0.76 mm outside the 2.4 mm bar (was 1.8 / 0.6 mm); B.Cu peak 10.41 A/mm at (18.3,83.17) at 2.9 A (was 10.21); named POWER_NARROW entry, K-width's 2 mm rule holds.
- RAW_PROTECTED DC: U9.6 -> U400.2/3 37.77 -> 37.60 mOhm, U9.6 -> U11.2 7.05 -> 6.78 mOhm; U9 OUT via currents now 0.92 / 0.68 A at 1.6 A (was 1.13 / 0.47 A): the 0.7 mm leg to (21.1,78.25) shares current better.
- PORT_4V8 DC: U401 -> J410 2.37 -> 3.58 mOhm (OUT via moved 0.95 mm north), In2 neck 0.41 -> 0.75 mm; U401 -> J440 29.48 -> 30.57 mOhm, neck 0.57 -> 2.12 mm; largest via 1.51 A at 1.9 A.
- Hot-plug: re-extracted inputs are byte-identical to the committed hotplug_inputs.json and the re-run gives identical rows: 2304 cases, 0 failures, -14.807 V, 8.995 / 5.088 V/us.
- D402: closed-switch EN shift 5.685 mV and J400.2 5.216 V at 8.4 V confirmed; 14.3 mV C87 rise (150 pF x 21 V / 220 nF) confirmed as arithmetic (trigger tolerance an Inference, as stated); J400.2 stays below ESD103's 15 V VRWM up to the SMBJ12CA clamp (19.9 V x 0.62 = 12.3 V).
- U401 divider on B.Cu: no via between U401.3 / R402.2 / R403.1 (single-open test), R403.2 returns to U401.4; 4.792 V nominal (0.8 V x (1 + 49.9/10)); divider current 80 uA >= TI's 5 uA; FB run passes 0.175 mm from R402.1 (PORT_4V8), DRC-clean.
- TI SBVS282A 7.4.1.1 suggests R2 and CNR/SS return separately to the thermal pad with GND not tied to an external plane; a noise-performance recommendation the records do not claim to follow.
- C88.1 (0402, 0.5 mm land) is entered by the 0.7 mm feed, which overhangs the land 0.1 mm each side; the previous board did the same.
- In2 RAW_PROTECTED loses about 4.1 mm2 of fill round the ACT_GATE second barrels (x 10-16, y 71-73), off the U9 -> U11 / U400 current paths; K-plane OK, no RAW necks under 1 mm.
- Single-open tests (own graph tool, pads / tracks / vias / fills): ACT_GATE, BOOT0, VCAP2, VLOGIC (R60.1), LOGIC_SOURCE_ST, USB_LIMITED (U10.6 -> R87.1 at (16.0,28.0)), PORT_4V8 to each port and R402.1 and 3V3 (R91.1) stay joined with any one changed via open; USB_LIMITED (22.0,62.25) stays single, as D-R24-10 records.
- R10_VALIDATION 'Historical round10 deviations' section 4 still quotes older U9 entry, C88 neck, hot-plug and U402 via figures; the section is titled historical.
- M3_R10's 'C88.1 3.844 mm from the support (42,86)' sits under a heading bound to audit board 877d0199; C88 is now about 23 mm from that support (mechanics lens).

## Checks executed

- Board SHA-256 before and after (shasum -a 256): 1407e850... both times
- Copper / footprint diff against 9b27268 (board 5516eeec) with pcbnew (.supervisor/r24_power/cdiff.py -> cdiff.txt)
- Region dumps of the U9 west cell, J400 / D402, U401 divider, U400 input, R92 / TP88 (region.py)
- Via layer-connection report for 26 changed vias (viaconn.py) and other-net clearances by SHAPE.Collide bisection (clear.py)
- Single-via-open connectivity tests on ACT_GATE, BOOT0, VCAP2, VLOGIC, LOGIC_SOURCE_ST, USB_LIMITED, PORT_4V8 (each port, R402.1), 3V3, PORT_LDO_FB, BAT_SW_RETURN (singleopen.py)
- tools/dc_solve.py on both boards: BAT_IN J1.1->U9.5 at 2.9 A; RAW_PROTECTED U9.6->U400 at 1.6 A and ->U11.2 at 1.3 A; PORT_4V8 U401->J410 / J440 at 1.9 A (dc/*.txt)
- tools/r10_hotplug.py --extract into the probe dir (byte-identical to committed inputs) and the full nonlinear 2304-case re-run (identical rows)
- tools/check_r10.py --only K-plane,K-power,K-width,S-5,K-ports on the committed board (all OK; check_subset.json)
- In2 / In1 fill rasterisation and diff, 0.02 mm (zonepolys.py, rasterdiff.py)
- EN network corner model with and without D402 (en_d402.py) and bench-ramp threshold window (ramp_window.py)
- Datasheet reads: TI SLVSFC9C p9 thresholds and OVLO; Infineon ESD103 Rev 1.3 Table 3; TI SBVS282A pin table, eq. 3-4, 7.4.1.1

## Sources

- TI TPS25947 SLVSFC9C (https://www.ti.com/lit/ds/symlink/tps25947.pdf) p7, p9 (cached .supervisor/r14_parts_pdf/tps25947.pdf)
- Infineon ESD103-B1-02 series data sheet Rev 1.3, Table 3 p5 (LCSC C535146; cached .supervisor/r14_parts_pdf/infineon.pdf)
- TI TPS7A91 SBVS282A Table 4-1, equations 3-4, section 7.4.1.1 (cached .supervisor/r14_parts_pdf/tps7a91.pdf)
- R10_DECISIONS.md D-R19-10, D-R20-11, D-R24-01..17; round24_board_cad.md; docs/M3_R10.md, ORDERING.md 8.3, REQUIREMENTS.md F4 / F6 / F9, R10_VALIDATION.md, AGENTS.md

## Coverage limits

- No physical, thermal or scope measurement; DC solves use 20 C copper, 0.3 mm via barrels for every via and no pad-to-part resistance (dc_solve assumptions).
- D402 leakage below 15 V and at 85 C is not specified by Infineon; the 50 nA bound is applied at all voltages, as D-R24-11 does.
- GND single-open for U402.2 checked by layer connection only, not by the graph test (net too large); U402.2 is covered by check_r10 K-power.
- Only power-lens rails and the D-R24 changes in the brief were traced; fire-path and AGENTS section 2 analysis is the safety lens.
