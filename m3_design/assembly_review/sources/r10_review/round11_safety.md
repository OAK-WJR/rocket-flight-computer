# Round 11 — safety lens

Target: committed `21bc3b2`, PCB SHA-256 `0c50b9fd0930f34edab7129fc21b8e71d0ee03bc079e1900b7e131cece6bfaf8`.
Read-only review, 2026-10-29. No other round-11 report was read. No CAD, generator, supervisor request or Git state was changed.

**Totals: 0 Critical, 0 Major, 1 Minor group.** No change to AGENTS §2 is needed. Existing accepted architecture risks and explicitly unperformed qualification are not counted again as design defects.

## R11-SAF-01 — refresh the safety procedure and fire-budget records for the moved cells

**Minor; records only.** ORDERING §8 identifies old snapshots as historical, but the retained executable coating/probing instructions still mix their coordinates and population with the AVA board. The unchanged part-level instructions preserve the intended protections; this is not evidence of an observed unsafe assembly or a CAD failure. Refresh before using the instructions on an assembly.

- `docs/ORDERING.md:277–284`: the bottom coating envelope ends at x=26.8, but the retained ARM bank now includes R132/R175 at x=28 and R133/R180 GND pad centres at x=28.86. The list also retains removed C122/R124/R125/R177/R182. TP121 is called top-side, whereas native TP121 is **B.Cu (10.5,71.5)**. Use current per-part envelopes and current copper, retain U4/U5 exclusions and the controlled TP122 process, and regenerate the figure/list. Do not coat a guessed historical rectangle.
- `docs/ORDERING.md:284`: the NRST probe is specified as C24.1 (25.33,49.1), and GND probes as top TP74 (41.9,53.5)/TP88 (44.5,76.3). Native values are **C24.1 (25.45,49.42), B.Cu; C15.1 3V3 (29.05,47.82), B.Cu; TP74 GND (42.5,58.0), B.Cu; TP88 GND (35.5,87), F.Cu**. Update all current probe/trace references together. TP122 remains B.Cu (13.3,53.3).
- `m3_design/r10_parts.py:336–337`, `sources/r10_design/parts_budget.json:275–307` and `parts_qualification.md:267–273`: the fire calculation still uses circuit-pass lengths. The native current path sums are BAT_IN **6.000 mm at 1.0 mm**, RAW_ACT **5.886133 mm at 0.5 mm**, IGN **10.396068 mm at 0.5 mm**, OUT **7.954478 mm at 0.5 mm**. In particular IGN is no longer 4.85 mm. Keep the conservative 2.2 mm/0.4 mm single source-leg path (Q120.3 → common bar → Q121.2), without parallel credit. At the existing 35 µm / 1.72e-8 Ω·m material assumptions these give **29.472622 mΩ at 20°C / 35.263992 mΩ at 70°C**, replacing 25.176022/30.123110 mΩ. Re-solving the same coupled-load equation gives idle/one/two/three/four-stall currents **1.544322 / 1.479396 / 1.414223 / 1.348767 / 1.282976 A**. The worst remains above the selected **1.125 A** criterion, so this bounded correction does not establish a Major. Extract these values from the rebuilt board rather than leaving unbound geometry literals, then regenerate the related records. Material, FET, harness and source limits remain Calc/Inference.

All native coordinates above were read directly using pcbnew; current circuit roles were cross-checked against `schematic.net.xml` and `r10_route_pyro.py`. This group may duplicate the requirements, power or documentation lenses; count it once after consolidation.

## Safety coverage and evidence

| Check | Result |
|---|---|
| AGENTS §2 and newest owner decisions | Single-switch rule, two MCU controls, ground hard refusals, launch detection, in-flight sense-never-veto and explicit inference labels preserved. AVA's separate ARM connection is acknowledged in the owner record; the owner's subsequent instruction keeps one switch. |
| Native firing topology | J1.1 BAT_IN → Q120 D; Q120/Q121 common S = ACT_FET_S; Q121 D = RAW_ACT; R134.2 RAW_ACT → 2 Ω → R134.1/J121.2 IGN; J121.1 OUT → Q124 D, Q124 S → GND. No J124, former PYRO1_BUS or direct battery bypass found. |
| Independent enable | U1.16 PC1 → R122 1 kΩ → Q122 gate; R123 100 kΩ to GND. Q122 drives ACT_GATE through R121 10 kΩ. R120 100 kΩ/C120 1 µF connect ACT_GATE to the common P-FET source. Native Q120/Q121 are AONR21357 with source pins1–3, gate4, drain5–9. |
| Firing gate | U1.3 PE4 → R126 220 Ω → Q124 gate; R127 1 kΩ on the MCU side; R128 10 kΩ/C126 220 nF gate-to-GND. Q124 is AON7524. No reset pull-up was found. MCU analog-reset behavior agrees with the external pull-down topology; transient off behavior remains a bench obligation. |
| Safety contract run | Imported `check_r10.check_board` on the native board with `only={S-1,…,S-9}`: all nine pass, zero issues. S-4 checks 113 required contract parts and schematic population; BOM/CPL were not supplied in this lens. This subset is not a full check.sh or DRC result. |
| Barrels | Four current protected barrels pass S-8. Nearest foreign inner-copper gaps: OUT via (11.33,55.1) 2.479 mm; gate via (14.4,53.3) 2.100 mm to USB_LIMITED In2 track; J121.1 1.458 mm; J121.2 1.900 mm. GND and own-net exemptions remain explicit. |
| Single-resistor faults | Both native banks retain two separate 5.1 kΩ series tops, two separate 2 kΩ parallel bottoms and 10 nF filters, directly to PC0/PC5. With the adopted ±1.45% resistor corner, either one top short or one bottom open gives **3.342171 V at 19.9 V**, below the ADC-mode absolute limit 4 V. A top-short bank draws at most **1.397310 mA at 8.4 V**. Top-open, bottom-short and filter-short ground readings refuse on the ground; no two-fault guarantee is claimed. |
| Cold screen | Independent two-node reduction with 3.1 V diode-side bias, 10 kΩ cold resistor, two 11.2 kΩ banks, 2 Ω match and R134 2 Ω reproduces **99.368924/99.337881 mV CONT/BUS**. Open match gives 146.226415 mV CONT/bus≈0. Even the conservative 3.465 V/9.855 kΩ cold-bias current is only 0.352 mA, below the maker's 40 mA test maximum. These are conditional calculations, not firmware thresholds. |
| Required sequence | Current schematic notes `actuator_power.kicad_sch:1533–1547`, `mcu.kicad_sch:4701`, binding obligations and M3_R10 agree: both outputs low; passive cold screen before PC1; after prior enable ≥1 s plus observed discharge; then PC1 high/PE4 low ≥100 ms before powered checks. No prelaunch live-match firing test is permitted. |
| Fire timing | Recomputed 960 LSI cycles at 29.4–33.6 kHz =28.571–32.653 ms; 32.653+0.2+0.5+1.5=34.853 ms fits the 36 ms guarded intact-hardware contract. Normal physical current remains ≤20 ms including tail; never refresh during firing. LSI revision, reset latency, actual gate tail and resistor pulses remain unmeasured. |
| Back-feed | Always-on GPS/radio UARTs lack powered-off isolation; the camera retains its switch/translator. Current requirements prohibit USB/self-powered back-feed when attaching an e-match and require pack or match disconnected for USB bench work. J400 has no state sensor, so software cannot promise detection of an opening masked by back-feed. No conflicting shutdown guarantee was adopted. |

## Primary electrical sources checked

- [ST DS12110 Rev11](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf), §3.8 p32 (analog GPIO reset), Table9 pp64/67/70 and pinout (PE4/PC0/PC1/PC5), Table109–110 pp207–208 (ADC-mode 4 V/positive-injection limits), Table136 p233 (RevV LSI). Absolute limits do not guarantee valid ADC readings under fault.
- [AOS AONR21357 Rev2.1](https://www.aosmd.com/res/datasheets/AONR21357.pdf), pp1–2: P-FET pinout, −30 V drain/±25 V gate; [AOS AO3400A Rev3.1](https://www.aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf), pp1–2: driver pinout and 2.5 V gate characterization; [AOS AON7524 Rev1.1](https://www.aosmd.com/sites/default/files/res/datasheets/AON7524.pdf), pp1–2: N-FET pinout, 2.5 V on-resistance and gate-charge table.
- [MJG J-Tek LEAD-FREE technical sheet](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF), p1: 0.75 A all-fire is a 0.5 s test; 40 mA test maximum. This does not qualify the flight lot's 20 ms pulse.
- [Bourns CRM2512](https://www.bourns.com/docs/product-datasheets/CRM.pdf), pp1/3: 2 W at70°C and pulse graph. Graph interpolation and actual PCB thermal behavior remain inferences.

## Retained limitations, not new findings

No independent software safety follows from two outputs on one MCU. Trace/debug overrides, power attachment, reset, hot leakage, coating/rework and installed-radio disturbances still require dummy-load qualification. Default 0.15 mm surface spacing deliberately permits defects that can fire an enabled match or defeat the high-side gate; the barrel exclusion does not prevent OUT-to-GND faults. Mandatory local coating, final firmware checks and physical access/harness restrictions remain necessary. No R10 firmware or physical/e-match qualification is claimed.

For the refreshed deviation table, current same-face bare pad measurements include Q124.4→own drain **0.520 mm**, R126.2→Q124 drain **1.711 mm**, C126.1→Q124 drain **2.020 mm**, R128.1→LS120.1 3V3 **2.576 mm**, and TP122.1→C10.1 3V3A **1.745 mm**. These replace historical-coordinate examples; they do not add a new spacing requirement.
