# R8 plan: partial re-placement with planned-bus routing

## 1. Decision
Build R8 as **Strategy B** with C's plane and power rules and A's build hygiene. Two of three judges chose B: it has the best topology (MST 1731–1785 mm against C 1842 and A 2651; 110 inter-family crossings against 121 and 394) and keeps the most qualified geometry in place. Build it fresh as `m3_design/r8_build.sh` on branch `m3-assy-r8` from 431025d: no R7 patch stages, no autorouter, no hand-patched copper.

- **Rigid, unmoved, hash-asserted every stage:** RF strip copper, CH1 block copper, PYRO_BLOCK, J1, J122 and tie holes, M3 holes, outline. check_actuators, CH1_PADS, fit_check, DRU hashes and VEHICLE.md stay valid.
- **Re-placed:** U1 at rotation 0 (pins 51–75 face the strip); each block beside the U1 face it talks to (seed `partial/b0_place_final.tsv`); input protection at J1; camera supply beside J9; flash and Y1 under U1; TH1–TH3 removed.
- **Pins:** H0 RF map (SPI2 on PB10/PB11 with IOSWP, RXEN PD9, DIO1 PE15, GNSS PD14/PD15); camera UART off loader port USART3 to UART7 PE8/PE7; RADIO_NRST on loader-inert PE9; fewest follow-on moves; contract pins unchanged; R310 at the MCU end on 3V3.
- **From C:** In2 GND under the CH1 pads and barrels and every pyro/servo lane, RAW_ACT/BAT_IN islands ≥ 2.5 mm from pyro copper; FET sources facing, BAT_IN without series vias, multi-layer RAW_ACT; D121 on the bottom at J122 (check taps with `d121.py`); three fence openings, gaps ≤ 2.7 mm; keep-out-aware detour baseline; IMU toward the axis only if free.
- **From A:** keep-list hash, via columns ≥ 0.9 mm pitch, ACT_GATE on local B.Cu, A as fallback.
- **Not C:** it moves J122, the tie holes and J9, runs a 290 mm pyro corridor, and its RF and DC proofs used illegal or near-empty boards. **Not A:** its placement is within 3% of R7, so F9's hot-plug premise, P1-9 and the detours stay open.

## 2. Definition of done
**Hard gates:**
- check.sh 0 (DRC incl. A–H, connectivity, parity, ERC); check_r8; check_actuators unchanged; fit margins ≥ R7's; byte-identical rebuilds.
- route_check C1/C3/C4/C6 = 0, except owner-accepted inherent items (TXEN, A8).
- New checks: F10's 5 mm separation (counting R306/R313/R315 as RF parts); no inner RAW_ACT/BAT_IN within 2.5 mm of PYRO1_BUS/IGN/OUT; PYRO1_GATE_N ≥ 0.5 mm from servo PWM; a reset/loader pin table that allows only LEDs on loader-driven pins; S15 = S16 = 0.

**Scorecard targets** (`run_survey.sh`):

| Metric | R7 | Target |
|---|---|---|
| S1 signal track | 3355 mm | ≤ 2300 mm |
| S4 signal vias | 217 | ≤ 75 |
| S6 detour / S7 excess | 1.396 / 1081 mm | ≤ 1.18 / ≤ 350 mm |
| S8 / S9 | 23 / 12 | 0 / 0, except keep-out-forced nets |
| S10b bends | 648 | ≤ 400 |
| S12 critical layer changes | 73 | ≤ 32 |
| S17 placement MST | 2727 mm | ≤ 1850 mm |
| C2 info-only instances | 252 | ≤ 80 |
| P1 / P3b / P4 / P6 | 0.880 / 16 / 8 / 1581 mm | ≥ 0.90 / ≤ 4 / ≤ 5 / ≤ 900 mm |
| P7 / P9 / P10 | 32 / 6.1 / 13.8 mm | 0 / ≤ 3.5 / ≤ 7 mm |
| R1 / R3 | 60 / 116 mm | ≤ 5 / ≤ 15 mm |
| critical_reference | 27.9 % | ≤ 8 % |
| 7.7 A necks RAW / BAT / FET | 3.00 / 3.82 / 2.65 mm | ≥ 5.3 / 5.6 mm / owner threshold (pad-limited) |
| Simplicity index | 100 | ≤ 35 |

## 3. Steps
One agent per step; its verification must pass before the next starts.

0. **Owner decisions and datasheets.**
   - Out: `R8_DECISIONS.md`: U1 rotation, PB10/PB11 exception, R310 rail, D121, tooling holes, TP122 via (A8), detour baseline, FET rise threshold, IMU.
   - Out: `pin_table.tsv`, giving each moved pin's DS12110 AF, RM0433 IOSWP status and AN2606 loader state.
   - Verify: every row is cited; fallbacks are agreed up front (H1 map, or +2 vias without IOSWP).
1. **Gate tools first.**
   - Out: check_r8, the new checks, empty allowlist and leftover lists, the detour baseline, the hashes, and dc_neck and the scorecard moved into tools/.
   - Verify: tests pass; each new check fires on a seeded defect; independent review.
2. **Schematic** (`r8_sch.py`).
   - Verify: ERC 0, parity, the pin diff matches the decisions, no RF pin on a safety net.
3. **Spikes**, run in parallel, about one day each, with the rigid copper present:
   - (a) under U1: flash, Y1, decoupling, the QSPI/HSE/NRST/ARM1_SENSE dives;
   - (b) servo bus through D121 to J122;
   - (c) battery band: rule H, In2 islands, DRC A–H, dc_solve at 0.1 mm;
   - (d) RF buses with the status cluster placed legally.

   Verify: DRC 0, route_check 0 on spike nets. Kill: (a) → flash on top; (b) → relabel D121; (c) → C's battery corner; two fail → Strategy A. R7 stays orderable throughout.
4. **Placement freeze** (`r8_place.tsv`, legaliser modelling the 1.0 mm test-pad clearance and rule H).
   - Verify: DRC 0, fit, F10 separation, tab windows, MST ≤ 1850 mm, hashes.
5. **Power** (`r8_power.py`): In2 regions, 7.7 A copper and via fields.
   - Verify: DRC A–H, pyro-clearance check, dc_solve necks.
6. **Signal families**, one module each: rf_iface/gnss (port `rf_route.py`), usb_swd, qspi_hse, imu_i2c, servo, pyro_exits, camera, status. Then the remaining short links through a constrained r5_maze: ratio ≤ 1.3 and 0 extra vias, or the build fails.
   - Verify after each module: connectivity, DRC, route_check 0 on its nets, the asserted length and via budgets.
7. **Ground** (`r8_ground.py`): a GND via at every critical layer change, a stitching grid at ≤ 4 mm, the fence.
   - Verify: C6 = 0, P7 = 0, P9/P10, rf_gnd_reach, check_r8.
8. **Post and fab.**
   - Verify: full gate, rebuild SHA, cost $105.98 with 52 extended codes.
9. **Requalify:** DC at 0.05 mm with IPC; absolute critical reference; pyro exits, coating, leakage, A8 re-measure; RF tables; vibration; hot-plug; firmware binding; ORDERING, REQUIREMENTS, M3_R8, R8_VALIDATION.
   - Verify: every item on the survey's "invalidated by re-placement" list is closed with evidence.

## 4. Review loop
Independent reviewers each pass: pyro and arming safety; requirements traceability (F1–F10, P1–P3, M1–M3); RF; power, thermal and hot-plug; routing simplicity (dedicated reviewer); planes and return paths; DFM, fit and mechanical; build integrity (no tool weakened to pass). Fixes go only into tables or generators, then rebuild and rescore.

**Stop when** two consecutive passes find 0 Critical and 0 Major, every hard gate passes, and each remaining miss or Minor item has a measured cause that cannot be removed without a priority-1 cost. Record those items, then offer the owner a re-check.

## 5. Risks
Spikes cover under-U1 density and the servo and battery layouts; step 0 covers pin refusals. Also:
- **Power copper beside the pyro barrels:** In2 GND, the 2.5 mm gate, DRC A–H every stage.
- **ACT_FET_S neck limited by the FET pads:** sources facing, parallel layers, threshold agreed in step 0.
- **Tight F10 separation:** the automated 5 mm check; resistors ≥ 5 mm from U1.
- **Routing stalls:** bus primitives, maze acceptance, per-family gates.
- **Rigid copy drifts:** hashes, re-baselined only for the approved A8 edit.
- **KiCad bad_alloc:** rerun with PYTHONUNBUFFERED=1.
