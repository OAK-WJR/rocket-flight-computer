# Round 24 safety lens (Claude)

- Target: commit `f2b8251`, PCB `1407e8506efbac0f664b3aeb65568c32ae9670c9b45b502a465cba1130de522e`.
- The SHA-256 was the same before and after the review, and matches `git show f2b8251:` of the board.
- Rule: only real errors count. Full detail is in `round24_safety.json`; probe scripts and outputs are in
  `.supervisor/r24_safety/`.

**Totals: 0 Critical / 0 Major / 6 Minor.** No AGENTS section 2 violation was found. S-1 to S-9, K-actuators and
K-ports pass on the built board. No new single fault energises the bus, fires the match, or turns the board on with
J400 open. All six findings are record or calculation errors. Four are in the safety lens; two are outside it and
were found incidentally.

## Findings

| ID | Kind | Sev. | What is wrong | Key number |
|---|---|---|---|---|
| R24-SAFETY-01 | doc | Minor | The D-R24-17 chamfer of BAT_FAULT_N's F.Cu corner (16.55,83.35) moved that track closer to the BAT_ENABLE via (17.1,82.8). Five records still state 0.200 mm: M3_R10 (which says the gap was "re-measured on `1407e850…` … unchanged"), ORDERING 8.3's coating worksheet, FMEA H-6, owner row 24 and the R10_VALIDATION section 1 table. This is the latch leak path (EN held at up to 3.19 V). | 0.173 mm (pcbnew 0.174), was 0.200 |
| R24-SAFETY-02 | calc | Minor | D-R24-11 says the EN timing figures "stand" or "are kept", because D402's leakage is "a quarter of" the 0.1 µA that D-R20-11 already carries. That ±0.1 µA is U9's own EN leakage; D402's leakage is a second current on the same node, so the two add. D-R20-11's method, reproduced exactly, plus the record's own 5.7 mV gives: 8.5 → 8.3 ms at 5.73 V; 10 ms needs 5.94 V (5.96 V with the open-switch path), not 5.92 V; turn-off corner 4.778 → 4.802 V; turn-on up to 130 ms. | At F4's 5.92 V pack the worst case is 9.83 ms, under the 10 ms criterion |
| R24-SAFETY-03 | doc | Minor | The J400 first-article / post-discharge bench-ramp windows (turn-off 4.5–4.8 V, turn-on 4.9–5.2 V) exclude in-spec boards. They also contradict the battery_entry sheet note (on 4.89–5.05 V, off 4.45–4.61 V). Correct bands from TI p9 with the 1 % divider, ±0.1 µA EN leakage and D402's 50 nA: turn-on 4.72–5.25 V, turn-off 4.29–4.80 V. | VUVLO(F) 1.08 V on nominal parts turns off at 4.46 V |
| R24-SAFETY-04 | doc | Minor | Five records were not updated for D-R24-02 / -08. (a), (b): the R10_VALIDATION section 1 row and M3_R10 Firmware rule 4 still call Q120's gate a single via, with "respin: a second via". (c) M3_R10 Firmware rule 5 says "R91.1 and U1.28 each hang on one via"; the FMEA says the opposite. (d) The round 24 summary says the Q121 barrel (11.74,72.3) is 0.342 mm from "the nearest foreign copper"; GND fill is at 0.251 mm on both faces. (e) M3_R10 counts the R18_BARREL_KEEPOUT areas as eight; the board has ten. | No single via open splits ACT_GATE, U1.28 or R91.1 |
| R24-SAFETY-05 | doc | Minor | *(Outside the lens.)* M3_R10 Power still says via (30.575,11.6) joins U401's sense resistor R402.1 to In2. D-R24-09 removed that via; R402 now sits on the B.Cu OUT run. | The via is absent on `1407e850…` |
| R24-SAFETY-06 | doc | Minor | *(Outside the lens.)* REQUIREMENTS M1 cites `stock_check.json` 2026-10-31T23:23Z with U9 at 40 in stock / −69 orderable. The committed file is the 2026-11-02T01:42:53Z run, with 28 / −83. | 28 / −83 |

Fixes:

- **01:** correct the five texts to 0.173 mm. Alternatively, at the next board change, add a CHAMFER_CUTS entry of at
  most 0.32 mm for that corner, which restores 0.200 mm.
- **02:** recompute with D402's 50 nA and replace the figures: 10.3 / 20.1 / 26.0 ms; 8.2 ms at 5.73 V; 6.3 ms at
  5.5 V; minimum pack 5.96 V; turn-on 30–130 ms; turn-off corner 4.80 V. Strike "stand / kept".
- **03:** state the tolerance bands, or compare each board against its own first-article baseline.
- **04 to 06:** update the texts.

## Fix verification

| Decision | Measurement | Verdict |
|---|---|---|
| D-R24-02 Q120 / Q121 second barrels | Removing any one via leaves ACT_GATE joined. S-8 is 1.051 mm (In1 GND, In2 RAW_PROTECTED) at both new barrels, which have their own keep-outs. Q120.4 reaches R120 / C120, and Q121.4 reaches R119, on B.Cu with no barrel. Recorded gaps reproduce: 0.361 / 0.342 / 0.422 mm; hole edges 0.618 / 0.549 mm. | confirmed (records: 04) |
| D-R24-05 U9 west cell, EN path | EN still crosses one via (17.10,82.80), with 4 single opens between U9.1 and R81. C88 is at B(18.67,83.56) with C88.1 on U9.5's axis; its GND via is at (19.59,84.06). BAT_IN to EN: 0.200 mm (U9 land), 0.401 mm (EN stub), 0.487 mm (0.7 mm trunk, was 0.345), 0.500 mm (C88.1). But BAT_FAULT_N is now 0.173 mm from the EN via. | partly (01) |
| D-R24-11 D402 | Board, netlist, BOM and CPL agree. BAT_SW_RETURN = {J400.2, R165.1, D402.1}, D402.2 on GND. Tap 4.114 mm; GND via 0.7 mm away. Only GND copper is within 0.6 mm of the new BAT_SW_RETURN copper. D402 cannot turn the board on or keep it on. Shorted, EN sits at 0 V with J400 closed and the board cannot start (per-flight steps 3 and 5 see this). Open, the board is back to the unclamped state. The 5.7 mV figure reproduces. | partly (02) |
| D-R24-15 R92 / TP88 | Both are at their new positions, as in the probe worksheet. The tab rule areas and TAB_BANDS_R10 are unchanged. No safety copper is nearby. | confirmed |
| D-R24-17 on safety nets | S-9 holds. Across 18 pyro / arming / switch nets and 9 power nets, comparing the old and new boards, only one gap shrank (01) and two grew. | partly (01) |

## Checks executed

- SHA-256 of the board, before and after the review.
- pcbnew polygon-clearance inventory comparing `5516eeec…` and `1407e850…`.
- Independent S-8 measurement: 12 barrels on 6 nets, minimum 1.021 mm.
- Single-open connectivity checks: ACT_GATE, ACT_FET_S, BAT_ENABLE, BAT_SW_RETURN, LOGIC_SOURCE_ST, 3V3 at R91.1, and
  BAT_IN with C88.1 removed.
- `check_r10.py --only` S-1..S-9, K-actuators, K-ports: all OK. This was a read-only run with its report in the probe
  directory.
- The netlist, the sheet notes, and the BOM / CPL rows for D402.
- Datasheet pages: Infineon ESD103 Rev 1.3 Tables 2–4; TI SLVSFC9C pp. 7 and 9.
- Replication of D-R20-11's EN timing.
- Probe-worksheet positions.

## Observations (not counted): 11

Selected:

- A D402 left leaky by a discharge it absorbed (about 2 µA) has the consequence of outcome (b). The records list only
  the shorted and open modes.
- The new ACT_GATE via lands are 0.251 mm from the outer GND fills. This is the accepted surface class (owner row 2).
- The per-flight list can be carried out on this board as written; every probe position it names matches the board.

## Coverage limits

- No DRC, kicad-cli, hot-plug or ESD simulation.
- There is no D402 leakage figure at 85 °C.
- Routing hygiene and the fab package were left to other lenses.
- Firmware exists only as text, and no physical test has been run.
