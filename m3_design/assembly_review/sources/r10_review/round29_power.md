# R10 round 29, power lens (Claude)

Target: commit `09a564e`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (SHA-256 checked
before and after; unchanged; git state untouched). Probe directory: `.supervisor/r29_power/`.

## Totals

**0 Critical / 0 Major / 0 Minor.** No real error found in the lens.

## Findings

None.

## Fix verification

| Item | Measurement | Verdict |
|---|---|---|
| D-R28-01: one `port_A` = 1.461 A + AUX for `ports_w` and `loaded_pack` | Over round 28, `parts_budget.json` changes only lines 91–92. `power_budget()`, re-run on a byte-identical board copy, reproduces the file byte for byte (`42676342…`). Hand solve gives 5.880831 / 4.388491 V. | confirmed |
| D-R28-01 records (parts_qualification stall-input paragraph and GAP-1 SHA, STATUS, R10_VALIDATION) | 1.561 A = 1.461 + 0.1 A; 5.881 / 4.388 V; SHA `42676342…`. No current sibling still says 1.56 A or 4.389 V. | confirmed |
| D-R28-03 power labels in the binding note (AUX θJA, GAP-5, rule 4 VSD, rule 8) | Every label is present. GAP-5's 34.853 ms re-derived. | confirmed |
| D-R28-04 port-supply lead / audit A item 7 | 3.3 V / 196 V/s + 4 ms = 20.8 ms; 3.7 V / 166 V/s + 4 ms = 26.3 ms. 166–196 V/s is Table 9-1 scaled to 470 nF. U2's EN is tied to VIN, so UVLO 3.30–3.70 V governs. | confirmed |
| Audit A: USB attach inventory | VLOGIC 514.1 µF (C84, C6, C7, C99) plus C86 / C98 on USB_LIMITED = 516.1 µF; 2.4257 mC; 5.354–6.977 ms at 453.05 / 347.69 mA | confirmed |
| Audit A: C120 off τ | ACT_DRV is only {Q122.3, R121.2}, so C120 discharges through R119 ∥ R120: 64.52 ms (129.03 ms with one resistor open); 1 s = 15.5 / 7.75 τ | confirmed |
| Audit A: GAP-1 | 13.064091 W (12.370807 W without AUX); fire currents equal the budget | confirmed |
| Audit A: GAP-3 | 0.48965 W; 109.17–123.86 °C (70 °C bay) and 124.17–138.86 °C (85 °C); 112.32 °C/W; IGND 4 mA max | confirmed |
| Audit A: GAP-5 | 28.571–32.653 ms; 0.7392 ms tail; 34.8531 ms; Bourns 61.204 / 44.134 W; 1.233×; DS12110 Rev 8 Table 146 p238 read on the PDF | confirmed |
| Audit A: ride-through table | Every cell equals the budget; ports 9.856–10.822 W at 1.561 A; case (d) 0.561 A | confirmed |
| Audit A: OQ-5 | DS41326 Eq. 2 gives VOFF 5.7265 / 6.0115 / 6.2965 V and VON 6.4845–6.9405 V; 0.25 / 0.40 ms; 3.8 / 6.0 / 1.6 / 2.5 ms | confirmed |
| Audit A: shared port fault / upstream coordination | 2.911 / 3.160498 / 3.743861 / 4.420037 A; U9 3.946188–4.856999 A; AUX 4.641504 V | confirmed |

## Rails against limits (all pass)

- **K-power paths.** IPC-2152 floors at 30 °C: 0.68 / 0.326 / 0.157 / 0.167 / 0.299 / 0.356 mm, against drawn floors of 1.0 / 0.7 / 0.4 mm. `power_paths`, `fire_return` and `k_width` report 0 issues on the copy.
- **Regulator taps.** `single_via_opens` reports 0 issues. 23 extra in-memory taps (GND ties of U11 CP2 / OV2 / PR1, SS / dVdt / EN ties, port feeds) also survive any single via open, except the recorded U11.2 respin item and one MCU VDD pin.
- **Plane necks.** Only 3V3 In2 has necks under 1 mm: 0.549 / 0.549 / 0.589 / 0.706 mm, above IPC's 0.375 mm internal width at 2.0 A.
- **Hot-plug.** The inputs are bound to `a0ec075e…`, and their digest equals the results' `inputs_sha256`. Results: −14.807 V, 8.995 / 5.088 V/µs, 579.049 W / 2.979 mJ, retained 1643.90 µF and 5.914 V after 2 s. Against TPS25947's max(−15, VOUT − 21), the −15 V floor binds. ORDERING's ≥ 2 s wait matches.
- **Datasheet limits respected:**
  - TPS7A91: VIN 6.5 V, VOUT 5.2 V, no COUT maximum.
  - TPS2553: 2.5–6.5 V, RILIM 15–232 kΩ.
  - TPS2121: RILM 18–100 kΩ, VSS ≤ 4 V.
  - TPS25947: EN rec ≤ 5 V, OVLO 0.5–1.5 V, RILM ≥ 549 Ω.
  - Every MLCC, C84 and C85 is within its voltage rating.
- **EN model re-solved independently.** Every quoted figure (AGENTS, M3_R10, F6, ORDERING 8.3, binding note) matches:
  - drop-out 6.300 / 8.066 / 8.204 / 10.345 / 20.111 / 26.023 ms;
  - 10 ms floor 5.956 V;
  - turn-on 30.3–129.7 ms;
  - ramp 4.288–4.802 V (off) and 4.723–5.251 V (on).
- **USB-only, hold-up, PA6-trip and four-stall-plus-fire figures** all reproduce.

## Observations (not counted; 13 in the JSON)

1. A 6 V open pack with four stalls sags to 4.388 V (4.63 V with the camera shed). That is below U9's turn-off corner (4.505 V nominal, 4.802 V worst), so "retaining logic" does not hold there. The 6 V pack is below the Pack row's ≥ 7.4 V floor, which the requirement is checked at (5.881 V). Optional clarification.
2. Rule 4 / D-R23-02 quote 1.128 / 1.063 A. A re-solve gives 1.12747 / 1.06264 A: a 0.04 % model-precision difference, still above 1.125 A. The ratios hold.
3. Items already observed in earlier rounds: the 63.605 mm USB_LIMITED length (63.115 mm now), the U400 input feed outside K-power, and the U400 / L400 loss of 1.2–2.2 W.
4. Further observations: the PORT_5V3 design-current basis versus a single port short, the one-via feeds, the hot-plug retained-OUT limit, the datasheet confirmations and the reproduction records.

## Coverage limits

- No build, no `check.sh` and no hot-plug re-simulation.
- No DC or thermal copper solve.
- The DS12110 Rev 11 and SLVS841F pages were not re-read.
- The round 28 power report and the other round 29 lenses were not consulted.
