# Round 19 safety review (Claude)

Target commit `acba1969b42973aaf8d348dc6d2fce6b465fc1dd`, PCB `a3144b151b58daf8ba5747def50decc4d1751ad35be478fafc89ef53aa533918` (the same before and after this review). **0 Critical / 0 Major / 6 Minor.**

No inadvertent-fire path was found that fires the e-match with the bus disabled after one fault. The round 18 barrel keep-outs, R119, R123 and the R173 move measure as claimed. Two of the round 18 records overstate their claims, and the fix pass added one new exposure (TP121's stub).

## Method

- **Inputs.** Everything was read from the committed tree (`git archive acba196` into `.supervisor/r19_safety/`).
- **Netlist and DRC.** kicad-cli 10.0.7 netlist: 0 pad-net differences over 661 pads. Native DRC (all severities, schematic parity) on a copy: 0 / 0 / 0.
- **Own geometry code.** pcbnew 10.0.7 geometry export, with every distance computed by my own numpy code (no pcbnew collision helpers), on this board and on `632a9ad3`.
- **S-8, three ways.** My own numpy code, my own parser of the fabricated In1/In2 Gerbers (X2 net attributes), and the committed `check_r10.s8`. The S-8 numbers are unchanged after refilling a copy.
- **Other analyses.** An adjacency inventory of 15 pyro and arming nets, single-open connectivity of the gate networks, a nodal solve of the sense readings, and a BOM/CPL cross-check of 37 safety parts.
- **Datasheets.** Cached maker PDFs: TPS25947 SLVSFC9C, TPS2121 SLVSEA3F, AO3400A Rev 3.1, AON7524 Rev 1.1, AONR21357 Rev 2.1, AP6320x, DS12110 Rev 8.

## Findings

**R19-SAF-01 (Minor, new). S-8 still exempts GND at the PYRO1_OUT barrels.**
- **Where.** The OUT via (11.630, 55.100) barrel is 0.251 mm from In1 GND and 0.251 mm from In2 GND. The J121.1 hole is 0.550 mm from GND; its own inner ring is 0.250 mm. All three methods agree.
- **Why it matters.** OUT is Q124's drain, so a short from OUT to GND bypasses Q124. With the bus enabled it fires the match (about 1.5 A). The committed gate comment says GND "holds them off" for the pyro bus nodes, which is wrong for OUT. D-R18-04 cleared exactly this 0.25 mm inner geometry to 1.05 mm at the ACT_GATE barrels, where one fault removes only the first of two barriers; at OUT it removes the last one.
- **Detection.** A static short is caught by the passive screen (CONT and BUS near 0). Only a defect that forms inside the armed window fires.
- **Fix.** Add PYRO1_OUT to BARREL_GND_HAZARD, add In1/In2 keep-outs, and adjust the slow-return list (fix-now below).

**R19-SAF-02 (Minor, new). The pad-arming switch J400 can be bypassed or latched.** U9's EN node has a 227 kΩ Thevenin source and a 300 kΩ pull-down. The table lists its four close neighbours and the harness case.

| Pair | Gap | What a bridge or leak does |
|---|---|---|
| U9.1 (EN) to BAT_IN, under the QFN | 0.200 mm | Board on with J400 open (bypass) for a leak ≤ 1.52–1.83 MΩ |
| BAT_ENABLE via (17.1, 82.8) to BAT_FAULT_N track | 0.200 mm | Once on, R89 to 3V3 holds EN at 3.19 V, so J400 cannot turn the board off; latch for a leak ≤ 0.58 MΩ |
| BAT_ENABLE via (19.675, 66.4) to R134.2 (RAW_ACT) | 0.300 mm | Once the bus is enabled, RAW_ACT holds EN on; latch for a leak ≤ 1.69–1.96 MΩ |
| R123.1 (ACT_EN) to the BAT_ENABLE track | 0.330 mm | Recorded as "U9 stays off". That is true only while PC1 is low; with PC1 high, EN sits at about 2.2 V and the board latches on |
| J400.2 lead chafed onto any pack-voltage lead | n/a (harness) | EN = 2.88 V: board on with the switch open |

- **Records gap.** Neither the coating worksheet nor deviation section 1 covers this class on R10 (R8 recorded it). The per-flight J121.2 check, made with J400 open, sees only a live bus. It never shows that the board is off, or that opening J400 turns it off.
- **Fix.** Move the BAT_ENABLE via (fix-now below); coat the EN network; add a per-flight "board off with J400 open, and off again after opening" check; route the switch pair apart from power leads; record the class.

**R19-SAF-03 (Minor, new; side effect of D-R18-02). TP121's new stub doubles ACT_GATE's exposure to GND.**
- **Where.** The 7.14 mm B.Cu stub (11.14, 70.0)–(4.0, 70.0) raises the ACT_GATE copper within 0.30 mm of GND from 6.277 to 12.872 mm. It also adds a new ACT_GATE to BAT_SW_SOURCE pair at 0.400 mm.
- **Why it matters.** The stub is the surface form of R18-SAF-01's hazard: ACT_GATE to GND turns the series pair on with the switch open.
- **Is it needed?** TP121 is coated with its cell, so it is a pre-coating probe only. R119.1 and C120.2 are bare ACT_GATE pads in the same cell.
- **Fix.** Delete TP121 and its stub (fix-now below).

**R19-SAF-04 (Minor, carried from R18-SAF-04's records point). Deviation section 1 cites a stale surface inventory.** It still quotes the post-R11 inventory (34 rows, minimum 0.150 mm). On this board the inventory is 49 rows (27 without GND), minimum 0.173 mm. These pairs are not recorded:

| Pair | Gap | Consequence (Calculation) |
|---|---|---|
| R134.2 to R81.2's GND fan-out via | 0.196 mm | With the bus enabled, about 23 A unfused through Q120/Q121, with R134 bypassed |
| RAW_ACT feed under R134 to R134.1 (IGN) | 0.367 mm | Bypasses R134 |
| RAW_ACT sense branch to USB_OVLO | 0.175 mm | 7.4–8.4 V on U11 OV2, absolute maximum 6 V (TPS2121 p6) |
| RAW_ACT sense branch to R87.1 (USB_LIMITED) | 0.225 mm | USB 5 V on the bus with PC1 low whenever USB is attached |

- **MID-corridor residual.** A MID–RAW_ACT bridge masks an open match. The cold readings become CONT/BUS 102.0 / 55.5 mV, against 96.2 / 96.1 healthy and 141.5 / 0 open. The powered CONT reads 1.213 V whether the match is open or intact.
- **Fix.** Replace the stale inventory with the current one and record these consequences.

**R19-SAF-05 (Minor, new). S-8 ignores the protected terminal pads' own inner rings.**
- **Where.** S-8 measures from the hole wall, but J121.1 and J400.2 carry Ø1.9 mm rings on the inner layers. Copper to copper on In2 is 0.750 mm (J400.2 to RAW_PROTECTED) and 0.803 mm (J121.1 to 3V3). Row 9 of the decision table reports +0.050 / +0.103 mm over the 1.0 mm floor.
- **J400.2 to RAW_PROTECTED.** A short latches U9 on.
- **J121.1 to 3V3.** With the bus enabled, a short drives the match into the 3V3 rail. The AP63203 regulator runs in PFM, so it does not sink current (Inference). The match then carries an estimated 0.3–0.8 A, against a 0.30 A no-fire rating.
- **Fix.** Either remove the unused inner layers on the J121 and J400 pads, or count the rings in S-8; then correct row 9.

**R19-SAF-06 (Minor, carried from R18-SAF-03). The scope of AGENTS 2.4 is still unstated for Q122.** Q122 has R123 and R122 but no gate-source capacitor; its intent is met (gate node ≤ 2 kΩ). Fix: one scope line in REQUIREMENTS F8.

## Round 18 fix verification

| Fix | Verdict | Note |
|---|---|---|
| D-R18-01 (R123 2 kΩ, V3V3_SENSE removed) | confirmed | 0.218 V and 0.554 V reproduced. The 0.65 V threshold is a 25 °C figure. |
| D-R18-02 (R119) | partly | Via independence confirmed. "Any single via **or track** open" is too broad: two B.Cu segments (1.385 mm and 1.100 mm) between Q121.4 and R119.1 still float Q121's gate if open. TP121 side effect: R19-SAF-03. |
| D-R18-03 (PC1 run re-spaced) | partly | All gaps reproduced. "U9 stays off" holds only while PC1 is low. |
| D-R18-04 (barrel keep-outs) | confirmed | 0.251 → 1.050 mm everywhere claimed, by three methods. The GND exemption at OUT (SAF-01) and the rings (SAF-05) remain. |
| D-R18-05 (R173 at the OUT end) | confirmed | 2.825 / 1.577 / 0.575 mm; residuals 0.250 / 0.175 mm; OUT–GND 0.177 / 0.180 mm. Masking residual: SAF-04. |
| D-R18-06 (In2 3V3 fill) | confirmed | One piece, 1466.5 mm² (area only). |
| D-R18-10 (switch note text) | confirmed | Schematic text corrected. |

## Fix now

1. **R19-SAF-01.** BARREL_GND_HAZARD += PYRO1_OUT. In1/In2 fill keep-outs of radius 1.20 mm at (11.630, 55.100) and 1.70 mm at J121.1 (2.00 mm if the ring stays). Add PYRO1_OUT to the slow-return list, or exempt keep-out voids in K-region.
2. **R19-SAF-02.** Move the BAT_ENABLE via (19.675, 66.400) to (19.675, 66.600), with the F.Cu stub to 66.6 and B.Cu (19.675, 66.6)–(21.0, 67.925)–(21.0, 68.6). This gives 0.300 → 0.500 mm to R134.2, with every other gap ≥ 0.425 mm.
3. **R19-SAF-03.** Delete TP121 and its stub, update ACT_NETS and the probe tables. ACT_GATE exposure falls from 12.872 to 7.629 mm.

Full evidence, rejected candidates and coverage limits are in `round19_safety.json`; the scripts and outputs are in `.supervisor/r19_safety/`.
