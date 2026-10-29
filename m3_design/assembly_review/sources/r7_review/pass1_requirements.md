# R7 review pass 1: requirement conformance and procurement

Reviewer focus: REQUIREMENTS.md conformance, the F10/P1/M3 change list, live JLCPCB stock and cost.
Read-only review of branch `m3-assy-r7` (commit `3b215ba` plus the uncommitted 2026-10-15 edit to
`docs/REQUIREMENTS.md`). Board `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`184a87e84e67576341244c82517de3e9f55f5c1c22995dfad83631d48c856680` (the "Final R6 CAD validation" board).
No repository file other than this report was changed; `tools/jlc_cost.py` and `tools/jlc_stock.py` were run
against a scratch copy of the fab BOM/CPL, and the board was only loaded in memory.

Evidence gathered 2026-10-15 (UTC):

- `tools/check.sh` (20:1x Z): DRC 0, unconnected 0, schematic parity 0, ERC 0; metadata/model audit OK;
  silkscreen 0 points outside; R6 CAD contract OK (note: "100 mm length is outside the 80–90 mm target");
  actuator contract OK; fit check OK (worst J9 mated 0.03 mm; bottom support clearance C76 4.150 mm; top
  LED2.2 3.800 mm).
- `tools/fab_manifest.py`: OK, 5 outputs match the CAD. `tools/jlc_orient.py --verify-cpl`: 105 top + 109
  bottom rows rebuilt from JLC footprints, worst residual 0.491 mm, no errors, 8 placement-only (J1, R72, R74,
  R77, R100, R101, R103, R110).
- `tools/check_procurement.py` (with and without `--cost-only`): FAIL, stored `cost_check.json` supplier data
  (2026-10-13T19:17Z) is older than 24 h.
- Live JLC API (`selectSmtComponentList`, `searchType` 2): all 82 BOM codes 20:20:23–20:21:21 Z; RF and IMU
  candidates 20:23:53 Z and 20:37:58 Z. `tools/jlc_cost.py` on the scratch copy: **$84.40/board, 48 extended
  codes**; `tools/jlc_stock.py`: **short: C26633007 U4 stock 0 < 5**, thin: none.

"ATP" below is JLC's `canPresaleNumber` field. Reading it as available-to-promise (stock minus reservations)
is an Inference: it tracks about 75–95 % of stock on high-stock parts and is negative on parts with backorders.

## 1. Summary

- **F10 fails, as expected.** The CAD is still the external-port design: J130 (SH7) and J131 (SH4), the
  reset-off 4.8 V port supply (U16 → U14/L4 → U15) and 1 kΩ + SRV05 harness protection. There are 36 BOM parts
  plus TP130 on sheet 15, 583 track segments and 105 vias on TLM_/RADIO_/GPS_ nets, and no MAX-F10S,
  E22-900MM22S, SMA or GCPW. §5 gives the full remove/add list, the nets and the MCU pin contract.
- **M1 fails on stock.** U4 LSM6DSV320XTR (C26633007) has JLC stock 0 (ATP −33) and LCSC stock 0. No
  in-stock pin- and footprint-compatible part keeps ±16 g/±320 g/±4000 dps. The ST eStore lists the exact part
  "In stock" at $8.48 each for 5–9, so consignment is the practical route (§6.3).
- **The acceptance tooling still encodes the superseded requirements.** It has the 110 mm maximum, the 80–90 mm
  target, the J130/J131/TLM contracts and the $84.41/48-code targets. An F10-compliant board (estimated
  $115.60/board, 49 extended codes) would fail `check.sh` and the procurement gate until those are updated (§5.6).
- **F10 text needs tightening before layout:**
  - antenna-bias short-circuit limit (Major);
  - an RF-immunity requirement for the pyro channel (Major);
  - the GPS UART must not stay on USART1, a ROM-bootloader interface, now that the GPS is always powered;
  - the pi-network cannot take a SAW;
  - the E22-900M22S is not a footprint alternate.
- **ORDERING.md still describes the R5 board** (CH2 terminals, orange igniter, MLT-8530, J1 at the aft edge).
- **Cost:** removing the port parts saves $5.77/board (4 codes, 3 extended). The recommended RF parts add
  $36.97. The estimate is **$115.60/board, 86 codes, 49 extended**, against the $126.41/52 cap: margin $10.81
  and 3 codes.

Counts: **Critical 0, Major 6, Minor 12.**

## 2. Findings

| ID | Sev. | Requirement | Finding | Evidence | Recommended fix |
|---|---|---|---|---|---|
| R7P1-01 | Major | F10 | The CAD implements the superseded external-port design. It has no on-board GPS, radio, SMA, bias feed or pi-network. | Exported netlist, sheet "15, Telemetry radio and GPS port": J130/J131, U14 AP63301, L4, U15 TPS2553, U16 TPS259570, D130/D131, R190–R206, C170–C180, TP130. U1.63–69 carry the UART/mode nets and U1.51/U1.31 the port enable and fault. `check_r6.py` and `check_actuators.py` pass only because they still require these ports. | Apply the change list in §5. |
| R7P1-02 | Major | M1 ("every part in stock for 5 boards") | U4 LSM6DSV320XTR C26633007 is short: JLC stock 0, ATP −33, LCSC stock 0. Same-package ST parts all reduce the range: LSM6DSV80XTR (±80 g) C46898862 stock 0; ISM6HG256XTR (±256 g) C51931514 stock 1; LSM6DSV32XTR (±32 g) C22461202 stock 5,310. None is proposed. | JLC API 2026-10-15T20:20Z; lcsc.com/product-detail/C26633007 (`stockNumber` 0); estore.st.com LSM6DSV320XTR page: "In stock", $8.48 each at 5–9. | Buy 7–10 (attrition spares) from ST eStore or another franchised distributor, and order U4 as a JLC consigned part. Alternatively, if JLC can source it, use a JLC parts pre-order or Global Sourcing. Add a reviewed consignment path to the stock gate (R7P1-18). Do not plan owner hand-fitting of this bottom-side LGA-14. |
| R7P1-03 | Major | F10 ("bias feed … switched by LNA_EN, with current limiting") | The text does not bound the short-circuit current. u-blox's own feed (R8 = 10 Ω, L4, C14, P/N switch) lets a shorted antenna or coax draw about 3.2 V / 10 Ω ≈ 0.32 A from VCC_RF. That exceeds VCC_RF's 50 mA operating maximum and its absolute maximum (200 mA MAX-F10S, 100 mA MAX-M10S). u-blox relies on the antenna supervisor to switch the feed off when it detects a short. | MAX-F10S DS R03 Tables 12–13; MAX-M10S DS R03 Tables 11–12; MAX-F10S IM R01 §3.3.1.2 (two-pin supervisor), §4.3.4 ("R8 limits the short-circuit current"), Tables 38 and 40–45. | Require the u-blox two-pin supervisor: T1/T2 switch on LNA_EN, R8 10 Ω 0.25 W, L4 47 nH, C14 10 nF, and the antenna-side node of R8 to EXTINT (PIO5), with CFG-HW-ANT_CFG_SHORTDET/PWRDOWN/RECOVER per IM Table 38. Otherwise require any feed whose steady short-circuit current is ≤ 50 mA. Put the feed point on the SMA side of a DC block (§5.2). |
| R7P1-04 | Major | F8 (Tripoli/NAR) / F10 | The board now carries a +22 dBm (≈ 160 mW) transmitter, but no requirement covers pyro-channel immunity to it, and F10's separation list (bucks, MCU, fast digital) omits the pyro block. FMEA I-11/V-19 already says "transmit/harness immunity … still need dummy-load tests", but neither F8 nor F10 carries that requirement. | REQUIREMENTS F8, F10; FMEA_REDUNDANCY.md line 18. | Add to F8: with the radio transmitting continuously at full power into its flight antenna (and into a load at its SMA), armed dummy loads do not fire and the ARM/continuity readings stay valid (bench, ORDERING §5). Add to F10: the RF strip, SMAs and coax are kept away from the pyro block and igniter terminals. The distance is an owner/RF choice; ≥ 10 mm is a reasonable starting point (Inference). |
| R7P1-05 | Major | P1, M3, F10 (acceptance gate) | The gate and procurement tools enforce superseded requirements, so a compliant R7 board fails `check.sh` and procurement. | `check_r6.py` L24–39, 275–301, 309 (`length > 110.01`), 311 (80–90 note), 313–319 (J9/J130/J131 edge block), 391–392 (J130/J131 legends). `fit_check.py` L41–50, 58, 325, 339–340 (110 mm), 349, 385. `check_actuators.py` L2, 137–144 (PINNED), 378–385, 389–395, 398–408, 411–428 (TLM/port rules). `jlc_cost.py` L2, 16, 51, 100–101 (84.41/48). `check_procurement.py` L33–36, 68. Tests: `test_procurement.py` L122, `test_fit_check.py` L81, 199–201, `test_r6_check.py` L207–208, `test_fab_validation.py` L104–110. | Update in the same change as the CAD (§5.6), with tests for the new contract. |
| R7P1-06 | Major | M1 (ordering) | `docs/ORDERING.md` is still the R5 order and was not updated for R6 (last commit `580d358`). It lists CH2 terminals J120/J125 and orange igniter C430603, but J121 is now black C430601 by contract. It still has the MLT-8530 reflow limits (LS120 is now MLT-5020), "J1 toward the aft edge" and "Y = 0 is the battery-terminal end with J1" (in R6, J1 sits at y = 92.4 with its entry facing y = 100), the R5 part counts (93/116), and J120.1 in the hand-finish list. Order remarks are what JLC acts on. | ORDERING.md L1, 56, 61, 66, 70–76, 91, 108, 141–142; BOM rows J121/J124 C430601; `check_actuators.py` rule 11. | Rewrite ORDERING for R7 before any quote. Add the RF items: modules on the top side, MAX-F10S MSL 4, SMA straddle joints hand-soldered, rails and tabs on the long edges only, stackup and impedance (R7P1-14). |
| R7P1-07 | Minor | F10 / F9 (USB configuration) | Keeping the R6 GPS UART (USART1, PA9/PA10) with an always-powered GPS conflicts with the repository's own pin rule. The frozen design records "Never use USART1 (PA9/PA10): the ROM bootloader arms every interface at once … the GPS stream would hijack DFU", and the DFU path is a firmware jump to the ROM bootloader. R6 avoided this only because port power was reset-off. | ROCKET_FC_FROZEN_DESIGN.md §3.7 and §3.10 (AN2606 Table 113; not re-read here); ST open pin data for STM32H743VITx (PC6 USART6_TX, PC7 USART6_RX); `m3_firmware/pins_gnss.json` already binds GPS to PC6/PC7. | Put the GPS on USART6 PC6/PC7 (U1.63/64, freed by the radio) and leave PA9/PA10 unconnected. This needs no extra parts and matches the existing GNSS bench driver. Firmware can still hold GPS RESET_N low before a bootloader jump. |
| R7P1-08 | Minor | F10 (pi-network) | "Pi-network footprint (series 0 Ω fitted, shunts not fitted) so a filter can be added without a respin" holds only for lumped LC parts. A packaged SAW needs its own land pattern. The no-respin fallback for the 34 dB isolation goal is therefore limited. | F10 text; u-blox IMs show the SAW as a separate package. | Reword: "…so a lumped LC filter or match can be added without a respin; a SAW cannot be fitted on these lands". If a SAW fallback is wanted, add a dual-band SAW land with a 0 Ω bypass now. |
| R7P1-09 | Minor | F10 (radio alternate) | The E22-900M22S is 20 × 14 mm with a different land pattern, so it is not a drop-in for the 10 × 10 mm E22-900MM22S. Its JLC ATP is also −73 (stock 32, minimum 2). | JLC: C411293 "SMD,20x14mm", EasyEDA "WIRELM-SMD_E22-900M22S"; C5333985 "SMD,10x10mm", "WIRELM-SMD_20P-L10.0-W10.0-P1.27-TL". | State "layout alternate only (respin)". Reserve MM22S stock at order time. |
| R7P1-10 | Minor | F10 (isolation) | The 34 dB budget uses the MAX-M10S's −12 dBm at 915 MHz. MAX-F10S immunity data are "currently not available", and RF_IN is rated 0 dBm absolute maximum on both parts. Swapping the two antenna leads would put +22 dBm into the GPS antenna's LNA output and the 3.2 V antenna bias onto the 915 MHz antenna. | MAX-F10S IM R01 §4.3.2; MAX-M10S IM R01 Table 6; DS absolute-maximum tables. | Say the bench C/N0 test is the only evidence for the MAX-F10S. Label the SMAs "GPS" and "915". Consider RP-SMA on the radio port so the leads cannot be swapped (Inference). |
| R7P1-11 | Minor | F6, F9, F10 (power), pad-time row | The F10 power text lacks the new parts' supply limits: GPS VCC/V_IO ≤ 3.6 V absolute maximum (radio 3.7 V); MAX-F10S start-up inrush up to 100 mA; VCC/V_IO ramp limits of 25 µs/V–35 ms/V ("exceeding … may permanently damage"). The F6 battery-lead hold-up (5–15 ms on C84) and the pad-time figure (290 mA, "peripherals on") predate the on-board RF load. A USB-only bench run with the radio transmitting goes through U10, whose limit is set by R85 66.5 kΩ (351–449 mA per the contract text for the same resistor); that budget is unchecked (Inference). | MAX-F10S DS Tables 12–13 and §4.3; MAX-M10S DS Table 11; EBYTE E22-900MM22S DS §2.1–2.2; REQUIREMENTS F6, pad-time row. | Add the limits to F10 and F9, and recompute F6 hold-up, the pad-time row and the USB-only budget with continuous TX (Calc). Refer this to the electrical reviewer. |
| R7P1-12 | Minor | M3 text | The SMA sentence is wrong for procurement. Cinch 142-0701-801 C3173345 has 2 in stock against 10 needed (short), while Molex 73251-1150 C841205 has 211 at $3.89, XUNPU SMA-KE-347-H13.5-1.6 C5723200 has 1,498 at $0.41 and BAT WIRELESS BWSMA-KE-P001 C496550 has 73,004 at $0.32. Today's removal saving is $5.77 and 4 codes (3 extended), not $6.27. M3 also still says "R6 must not cost more". | JLC API 2026-10-15; §7. | Use the wording in §4. |
| R7P1-13 | Minor | M1 (reflow ratings) | LS120 MLT-5020 (C94598) has no recorded reflow rating; M1 itself says "the replacement LS120 needs its own verified profile". Its datasheet's reflow test (item 9) is a figure that could not be read as text. ORDERING still cites the MLT-8530's 250 °C / 10 s. | `procurement_catalog.json` C94598 records dimensions only; LCSC datasheet C94598. | Read the profile figure, record it in the catalog and ORDERING, and keep 240 ± 5 °C Standard PCBA. |
| R7P1-14 | Minor | M1 / F10 (RF manufacturing) | F10 sizes the GCPW "for the ordered stackup", but no stackup or impedance option is ordered: ORDERING says "Impedance control: Not specified". The KiCad stackup is 0.2104/1.0392/0.2104 mm. u-blox says the modules go on the top side during reflow. MAX-F10S is MSL 4. | ORDERING §3; `m3.kicad_pcb` stackup; MAX-F10S DS Table 22; MAX-F10S IM §5 and MAX-M10S IM §4 (reflow: peak 245 °C, modules on the topside). | Name the JLC stackup (e.g. JLC04161H-7628) and impedance control in M1/ORDERING. Require U17/U18 on F.Cu. Add an MSL handling remark. |
| R7P1-15 | Minor | M1 (new part stock) | MAX-F10S C30005563 has 18 in stock but ATP 9 for 5 needed (thin; Inference). The fallback MAX-M10S C4153167 (1,136, ATP 1,050) fits the same pads but wants the 27 nH bias inductor. | JLC API; MAX-M10S IM R01 Table 10 (27 nH) and MAX-F10S IM R01 Table 42 (47 nH). | Reserve the MAX-F10S when ordering (JLC parts pre-order). Document the M10S fallback as a BOM change: U17 → C4153167 and L5 → LQG15HS27NJ02D C12669, same 0402 land. |
| R7P1-16 | Minor | Records | REQUIREMENTS L105–180 hold R6 checkpoint logs, duplicated in M3_R6.md. They contradict each other and the CAD: L120 says "TLM_FAULT_N remains PE0 / U1.97", while L156 and the CAD use PA7/U1.31. They also keep "cost ≤ $84.41/48", J130/J131 pinouts and "GPS maximum current is unpublished". STATUS.md and the top of M3_R6.md still say "R6 work stopped incomplete", against the final R6 validation. The AGENTS.md table is R5-era ("GNSS removed in R3", dual pyro). The FMEA I-11/V-19 row describes external ports. The bottom silkscreen says "M3-ASSY-R6". `m3_firmware/pins_gnss.json` and `pins_status.json` bind GPS to PC6/PC7 (R6 CAD: PA9/PA10). | Files and lines cited. | Move the logs into M3_R6.md, use "R7" naming, and update STATUS, AGENTS, FMEA and the silkscreen legend. Create a new firmware binding for R7 (AGENTS §3). |
| R7P1-17 | Minor | P1, P2, P3 | (a) P1 does not say whether "maximum 120 mm" includes the SMA overhang. (b) `fit_check` has no SMA/coax mated envelope. (c) P3 retention does not cover threaded RF joints. (d) Layout constraints: a forward extension (y 100 → 120) would block J1's wire entry, which faces +y (footprint arrows on local −y, rotation 180°). An aft extension invalidates the absolute-coordinate contracts unless the origin moves: the PYRO_BLOCK rectangle in `check_actuators.py`, RETENTION_HOLES in `fit_check.py`, the ORDERING tab windows, VEHICLE's mid support "(4, 46)" and AGENTS' "forward pair at y = 96.4". | `M3_DB128V_4P_Entry.kicad_mod` descr; J1 at (23.0, 92.4) rot 180; files cited. | P1: "board outline ≤ 120 mm; SMA bodies and mated plugs beyond the edge count in the bay stack". P2: add SMA plug + coax-bend envelopes. P3: SMA nuts torqued and witness-marked, each coax tied to the sled within about 2 cm (report). The layout reviewer picks the edge with these constraints. |
| R7P1-18 | Minor | M1/M3 tooling | `jlc_stock.py` has no consignment path, so a consigned U4 still fails the stock gate. The stored `cost_check.json` and `stock_check.json` are older than 24 h. | `jlc_stock.py` `stock_report`; `check_procurement.py` run (FAIL). | Add an explicit, reviewed consignment allowance (a field plus purchase evidence) and regenerate both reports immediately before ordering. |

## 3. Requirement walk (current CAD and gate output)

| Row | Status | Evidence |
|---|---|---|
| Sources: single primary pyro channel, isolated Blue Jay | Pass | `check_actuators`: no removed CH2 refs or PYRO2/ARM2 nets; PYRO1 nets exact. No backup interface (not CAD). |
| Sources: sensors for flight condition and roll (accel + baro, gyro) | Pass (parts) | U4 LSM6DSV320X on SPI1 (U1.89–91, CS PB7); U5 MS5611 on I2C1. |
| Sources: one board, 4-servo limit | Pass | J122 3×4 with SERVO1–4 on U1.22–25 (PA0–PA3, TIM2/TIM5 CH1–4 per ST open pin data). |
| Sources: radio and GPS on the board, uplink cannot arm or fire | **Fail** (on-board), Pass (no radio path to pyro) | External J130/J131 ports. Radio nets reach only U1 through R196–R200. |
| Sources: flight envelope, ≥ ±64 g, ±4000 dps, ≥ 10 km | Pass (parts); flight model not CAD | JLC C26633007 attributes "±320g", "±4000dps"; MS5611 to 10 mbar (frozen-design record). |
| F1 gyro ±4000 dps, error budget | Pass (part) / not verifiable in CAD | As above; budget is Calc/Bench. |
| F2 accel ≥ ±64 g + low-g channel | Pass (part); **procurement blocked** | ±16 g + ±320 g channels (JLC attributes); stock 0 (R7P1-02). |
| F3 barometer ≥ 10 km | Pass (part) | MS5611 10–1200 mbar (catalog datasheet link). |
| F4 four HV servo outputs, copper at 7.7 A | Pass for R6 CAD; Calc must be redone for R7 copper | `check_actuators` rule 7 (chain, 1k 0805, 10k pull-downs, RAW_ACT row); `r6_final_dc.json` (RAW_ACT 3.96 mΩ, BAT_IN 3.91 mΩ, ACT_FET_S 1.36 mΩ). |
| F5 ≥ 800 Hz IMU, 16 MB log | Pass (parts) | W25Q128JVSIQ on QSPI; IMU on SPI1. |
| F6 failsafe hardware | Pass (parts); Calc/Bench pending | Servo 10k pull-downs, pyro gate network, C24 100 nF on NRST (netlist). Hold-up numbers need re-derivation with the RF load (R7P1-11). |
| F7 one CH1 channel | Pass (CAD) | `check_actuators` rules 1–6c; Calc/Bench items not CAD. |
| F8 Tripoli/NAR pyro safety | Pass (CAD); text stale | ARM break, nets, DRU content and hash pinned, DRC 0. "Radio SH7 and GPS SH4 … edge block" is stale after F10; no RF-immunity requirement (R7P1-04). |
| F9 interfaces | Pass (CAD) | D8 SMBJ12CA BAT_IN–GND, R80/R165 470k, R167 10k bleed, J3 USB-C with VBUS_SENSE PD15, J9 GH4, J123, LS120 (`check_actuators` rules 9, 12–14b). Fault-case text does not yet cover GPS/radio pins (R7P1-11). |
| F10 on-board GPS/radio | **Fail** | R7P1-01. |
| P1 46 mm wide, ≤ 120 mm | Pass (46.00 × 100.00 mm) | `r6.json` outline [0, 0, 46, 100]. The tools still enforce 110 mm and print an 80–90 mm target (R7P1-05). |
| P2 bore fit, five supports | Pass (CAD envelopes) | `fit_check` OK; worst J9 mated margin 0.03 mm; supports (4, 4), (4, 46), (4, 96.4), (42, 96.4), (42.3, 4). Physical fit not verified. |
| P3 shock, retention, MEMS keep-out | Pass (CAD part); rest Bench | In-memory zone fill: no vias and no zone fill under the U4/U5 bodies on B.Cu (0.1 mm grid; only pad-escape track samples). |
| M1 stock for 5 boards | **Fail** | U4 short. |
| M1 placement rotations | Pass | `jlc_orient.py --verify-cpl`: no errors, 8 placement-only rows. |
| M1 reflow ratings | Not verified (LS120) | R7P1-13. |
| M2 JLC rules, silkscreen ≥ 1.0 mm / 0.15 mm | Pass | DRC 0 at all severities with `min_text_height` 1.0, `min_text_thickness` 0.15; `silk_check` 0. |
| M3 cost | Pass (old and new cap) | Live $84.40, 48 extended (old cap $84.41/48, 1 cent margin); R7 estimate $115.60, 49 (new cap $126.41/52). Stored evidence stale (R7P1-18). |
| Op. assumptions: pad time | Stale | "peripherals on" refers to the external modules (§4). |
| Op. assumptions: board position | Stale wording | "R5 fits the coupler bore…"; the R7 length changes the stack (parent VEHICLE). |
| R6 contract: `check.sh` zero | Pass | As in the header. |
| R6 contract: actuators and fit OK | Pass | As in the header. |
| R6 contract: no Critical/Major review findings | **Not met** | This pass (6 Major). |
| R6 contract: cost ≤ $84.41 and ≤ 48 codes | Pass today, by $0.01 | `jlc_cost.py` live. |
| R6 contract: fab outputs regenerated | Pass | `fab_manifest.py` OK. |
| R6 contract: preserve supports, CH1 spacing, guard clearances, thermal relief, no vias on TH pads, no overlap-only joints, flash bypass | Pass | `check_r6` OK; C29 1.88 mm / route 1.69 mm. |

## 4. Stale or contradictory REQUIREMENTS.md text and proposed wording

| Where | Current text (abridged) | Problem | Proposed |
|---|---|---|---|
| F4 (L54) | "Size and independently solve the final R6 copper …" | Revision naming | "…the final copper of the current revision (R7) …" |
| F8 (L58) | "Radio SH7 and GPS SH4 are keyed and share a separate edge block." | Ports removed by F10 | "The GPS and radio antenna ports are edge-launch SMA jacks on one short board edge, labelled GPS and 915 MHz; the two antenna leads should not be interchangeable (e.g. RP-SMA for the radio). With the radio transmitting continuously at full power into its flight antenna and into a load at its SMA, armed dummy loads do not fire and ARM/continuity readings stay valid (bench, ORDERING §5)." |
| F9 (L59) | "…no MCU or sensor pin exceeds its absolute maximum rating…" | New parts on 3V3 | "…no MCU, sensor, GPS or radio pin exceeds its absolute maximum rating (3V3 ≤ 3.6 V at the GPS, ≤ 3.7 V at the radio)…" |
| F10 GPS (L60) | "UART to the MCU plus RESET_N." | Bootloader conflict (R7P1-07) | "UART on USART6 (PC6/PC7), not on a ROM-bootloader USART, because the GPS is always powered; RESET_N to an MCU GPIO; SAFEBOOT_N to a test pad; V_BCKP and VIO_SEL open (3.3 V I/O)." |
| F10 pi-network (L60) | "…so a filter can be added without a respin." | SAW cannot fit 0402 lands | "…so a lumped LC filter or match can be added without a respin (a SAW cannot be fitted on these lands). Order: SMA, bias feed, 47 pF DC block, pi-network, RF_IN." |
| F10 bias (L60) | "Active-antenna bias feed from VCC_RF switched by LNA_EN, with current limiting." | Unbounded short current (R7P1-03) | "Active-antenna bias feed from VCC_RF through u-blox's two-pin antenna supervisor (MAX-F10S IM §3.3.1.2: switch on LNA_EN, R8 10 Ω, L4 47 nH, C14 10 nF, short sense to EXTINT), so a shorted antenna or coax is switched off; the steady short-circuit current from VCC_RF never exceeds 50 mA." |
| F10 radio alternate (L60) | "the E22-900M22S (C411293, 20 × 14 mm) is the alternate." | Not footprint-compatible | "…is a layout alternate only (different land pattern)." |
| F10 radio interface (L60) | "SPI plus NRST, BUSY, DIO1 and the module's RF-switch control lines." | Underspecified | "SPI, NRST, BUSY, DIO1 (EXTI-capable), RXEN from an MCU GPIO with a pull-down, TXEN driven by DIO2 (EBYTE §4.2), NSS pulled up so the radio is deselected while the MCU is in reset or the ROM bootloader." |
| F10 isolation (L60) | "(MAX-M10S tolerates about −12 dBm there)" | F10S data unpublished | "(MAX-M10S tolerates about −12 dBm there; MAX-F10S immunity is not published, so the bench test is the evidence; RF_IN is rated 0 dBm absolute maximum)" |
| F10 power (L60) | "both run from 3V3, which must carry about 0.15 A more…" | Missing limits | "…plus the GPS's 100 mA start-up inrush; 3V3 at the modules within 2.7–3.6 V, ramping 25 µs/V–35 ms/V (MAX-F10S DS)." |
| F10 RF layout (L60) | "RF parts ≥ 5 mm from bucks, the MCU and fast digital lines…" | Pyro block omitted | "…and kept clear of the pyro block and igniter terminals." |
| P1 (L66) | "maximum 120 mm … Record final outline … in M3_R6" | Overhang undefined; naming | "board outline maximum 120 mm (SMA bodies and mated plugs beyond the edge count in the bay stack, P2) … Record … in the revision record (M3_R7.md) and parent VEHICLE." |
| P2 (L67) | "…explicit GH/SH/servo/pull-pin mating envelopes … final R6 geometry" | SH gone; SMA missing | "…explicit GH, SMA-plug-with-coax-bend, servo and pull-pin envelopes … final R7 geometry." |
| P3 (L68) | "Mated connectors have external retention…" | Threaded RF joints | Add "SMA nuts torqued and witness-marked; each coax tied to the sled within about 2 cm of its jack." |
| M1 (L74) | No stackup; LS120 profile open | RF needs a defined stackup | Add "stackup JLC04161H-7628 (or as ordered) with impedance control for the two 50 Ω GCPW lines; GPS and radio on the top side; MAX-F10S MSL 4". Close the LS120 item. |
| M3 (L76) | "R6 must not cost more…"; "two edge-launch SMAs about $8–18 (in-stock choices are few: Cinch … $9.11 with 2 in stock)"; "saves about $6.27 and 3 extended codes" | Wrong availability; stale | "The board must not cost more…"; "two edge-launch SMAs $0.6–7.8 (Molex 73251-1150 C841205 211 in stock at $3.89; XUNPU C5723200 1,498 at $0.41; the Cinch C3173345 has 2, short for 5 boards)"; "saves $5.77/board and 4 codes, 3 of them extended (2026-10-15)". |
| Pad time (L83) | "…up to about 290 mA worst case on flight 2 (four idle servos, peripherals on)" | External modules | "…(four idle servos, GPS and active antenna on, radio receiving); re-derive with the radio's transmit duty cycle (118 mA at 3V3 while transmitting, ≈ 0.08 A at the pack, Inference)". |
| Board position (L86) | "R5 fits the coupler bore along its whole length" | Naming | "The current board fits…" |
| L105–111 | R6 implementation contract: "cost ≤ $84.41/board and ≤ 48 extended codes"; superseded port paragraph; "46 × 100 mm … 110 mm maximum … 80–90 mm" | Contradicts M3/P1/F10 | Replace with an R7 acceptance paragraph: `check.sh` zero under the R7 contracts; actuators/fit OK; no Critical/Major findings; M3 ($126.41, 52 codes) and M1 stock met; regenerated fab outputs. |
| L114–180 | R6 checkpoint logs | Duplicated in M3_R6.md; self-contradictory (TLM_FAULT_N PE0 vs PA7) | Delete from REQUIREMENTS (keep in M3_R6.md). |

## 5. Change list (F10, P1, M3)

### 5.1 Remove (sheet "15 | Telemetry radio and GPS port")

| Refs | Part | LCSC | Function | Code after removal |
|---|---|---|---|---|
| J130 | BM07B-SRSS-TB | C160393 | radio port | dropped |
| J131 | BM04B-SRSS-TB | C160390 | GPS port | dropped |
| U14 | AP63301WU-7 | C2158003 | 4.8 V port buck | kept (U8) |
| L4 | SRP5030T-6R8M | C1329837 | buck inductor | kept (L3) |
| U15 | TPS2553DBVR | C55266 | harness limiter | kept (U10) |
| U16 | TPS259570DSGR | C1849463 | port input limiter | kept (U7) |
| D130, D131 | SRV05-4.TCT | C13612 | port ESD | kept (D121) |
| R190, R206 | 300k 1% 0603 | C23024 | feedback | kept (R81) |
| R191 | 30k 1% 0603 | C22984 | feedback | dropped |
| R194 | 66.5k 1% 0603 | C137691 | U15 ILIM | kept (R85) |
| R195 | 4.42k 0.5% 0603 | C728617 | U16 ILIM | dropped |
| R192, R196–R202 | 1k 0402 | C11702 | enable / series | kept |
| R193, R203, R204, R205 | 10k 0402 | C25744 | enable pull-down, M0/M1 pull-downs, fault pull-up | kept |
| C170–C172 | 22 µF 1210 | C21397 | port buck | kept |
| C173, C175, C177, C179, C180 | 100 nF 0603 | C14663 | BST, output, U16 input, D130/D131 VDD | kept |
| C174 | 47 pF C0G 0603 | C1671 | FB feed-forward | kept (C77) |
| C176 | 1 µF 0603 | C29936 | TLM_5V | kept |
| C178 | 4.7 nF C0G 0603 | C85980 | U16 dV/dt | kept |
| TP130 | test pad | — | TLM_5V | — |

- **Nets deleted:** TLM_5V, TLM_5V_REG, TLM_SW, TLM_BST, TLM_FB, TLM_EN, TLM_PWR_EN, TLM_FAULT_N, TLM_ILIM,
  TLM_INPUT_ILIM, TLM_INPUT_LIMITED, TLM_DVDT; RADIO_M0/M1/RXD/TXD/AUX and their _MCU nets; GPS_RXD, GPS_TXD.
- **Copper:** 583 track segments and 105 vias on these nets (counted on the saved board).
- **MCU pins freed:** U1.31 PA7, U1.51 PB12, U1.63–66 PC6–PC9, U1.67 PA8, U1.68/69 PA9/PA10.
- **Net effect:** 36 BOM parts and 4 unique codes (3 extended) removed.

### 5.2 Add (recommended parts; stock and price in §6)

New references avoid the CH2 names that `check_r6.py`/`check_actuators.py` reject (Q125, TP123 and others).

| Ref | Part (MPN) | LCSC | Notes and source |
|---|---|---|---|
| U17 | u-blox MAX-F10S-00B | C30005563 (expand) | LCC-18; MAX-M10S-00B C4153167 same pins (DS tables 9/10); top side (MAX-F10S IM §5, MAX-M10S IM §4) |
| U18 | EBYTE E22-900MM22S | C5333985 (expand) | 20-pad 1.27 mm stamp-hole module, 10 × 10 × 2.5 mm; reflow peak 230–250 °C (DS §7.1) |
| J132, J133 | Molex 73251-1150 edge-launch SMA jack (GPS, radio) | C841205 (expand) | EasyEDA "SMA-SMD_3734660": centre pad 1 and grounds 2/3 on top, grounds 4/5 on the bottom, legs 8.5 mm apart. Board-thickness fit to be checked on Molex drawing 732511150_sd.pdf (not retrieved). Cheaper alternative XUNPU SMA-KE-347-H13.5-1.6 C5723200 (centre pad 5, legs 5.65 mm apart; different land). |
| L5 | Murata LQG15HS47NJ02D, 47 nH 0402 | C97998 (expand) | Bias-T (u-blox L4, IM Table 42) |
| Q126 | AO3401A P-FET (u-blox T1) | C15127 (base) | Discrete stand-in for Si1016X-T1-GE3 (C142570 stock 0, minimum 25); suitability is an Inference for the electrical reviewer. Alternative: TECH PUBLIC SI1016X-TP C50314620 (P+N pair; pin compatibility unverified). |
| Q127 | AO3400A N-FET (u-blox T2) | C20917 (base, existing code) | Gate on LNA_EN |
| R207 | 10 Ω 1206 0.25 W (u-blox R8) | C17903 (base) | Short-circuit limiter and sense |
| R208 | 100 kΩ 0402 (u-blox R7) | C25741 (existing) | T1 gate pull-up |
| C181 | 10 nF 0603 X7R (u-blox C14) | C57112 (existing) | Bias filter |
| C182 | 47 pF C0G 0402 DC block (u-blox C18 role) | C1567 (base) | Keeps antenna DC off the pi-network |
| R209 | 0 Ω 0402, pi series (fitted) | C17168 (base) | |
| C186, C187 | 0402 pi shunt lands | none | Set `dnp`, `exclude_from_bom` and `exclude_from_pos_files`. A DNP part without `exclude_from_bom` goes to `m3_bom_owner.csv` and needs an LCSC code (`export_fab.py`). |
| C183 | 100 nF 0402 at U17 VCC/V_IO | C307331 (existing) | |
| C184, C185 | 100 nF 0402 + 22 µF 0805 at U18 VCC | C307331, C45783 (existing) | EBYTE: "external ceramic filter capacitor is recommended" |
| R210 | 10 kΩ 0402 RADIO_NSS pull-up | C25744 (existing) | Radio deselected in reset/bootloader (Inference) |
| R211 | 10 kΩ 0402 RADIO_RXEN pull-down | C25744 (existing) | RF switch receive path off in reset (Inference) |
| TP131 | GPS_SAFEBOOT_N test pad | — | Recovery access; never loaded low at start-up (IM §3.2.3.3) |

- **Net effect:** 8 new codes (4 extended, 4 basic).
- **New footprints and models:** each new footprint needs its 3D model in `kilib/rocket.3dshapes`.
  `fit_check` fails on any non-DNP part without a readable model, and `quality_audit` checks model paths.

### 5.3 Nets and MCU pin contract (proposed)

Pin functions were verified against ST's STM32_open_pin_data (STM32H743VITx.xml). The bootloader reservations
come from ROCKET_FC_FROZEN_DESIGN.md §3.10, which cites AN2606 Table 113; AN2606 was not re-read here.

| Function | U1 pin | Module pin | Net | Note |
|---|---|---|---|---|
| GPS UART TX | 63 PC6 (USART6_TX) | U17.3 RXD | GPS_TX_MCU | Not a bootloader USART |
| GPS UART RX | 64 PC7 (USART6_RX) | U17.2 TXD | GPS_RX_MCU | |
| GPS reset | 65 PC8 (open-drain) | U17.9 RESET_N | GPS_RESET_N | Internal 7–13 kΩ pull-up; low ≥ 1 ms |
| Radio SPI | 52 PB13 SCK, 53 PB14 MISO, 54 PB15 MOSI | U18.15, U18.12, U18.13 | RADIO_SCK, RADIO_MISO, RADIO_MOSI | SPI2; keeps the radio off the IMU's SPI1 |
| Radio chip select | 51 PB12 | U18.14 | RADIO_NSS | Plus R210 pull-up |
| Radio DIO1 | 57 PD10 (EXTI10) | U18.20 | RADIO_DIO1 | Avoids EXTI1 (PD1) and EXTI14 (PULLPIN PC14) |
| Radio BUSY | 61 PD14 | U18.11 | RADIO_BUSY | |
| Radio reset | 67 PA8 | U18.3 | RADIO_NRST | |
| Radio RX switch | 66 PC9 | U18.10 | RADIO_RXEN | Plus R211 pull-down |
| Radio TX switch | — | U18.9 = U18.19 (DIO2) | RADIO_TXEN | EBYTE §4.2 |

- **GPS U17:**
  - pins 7 V_IO and 8 VCC on 3V3;
  - pins 1, 10 and 12 to GND;
  - pin 6 V_BCKP open;
  - pin 15 VIO_SEL open (the M10S IM R01 calls it "Reserved, leave open");
  - pins 16/17 SDA/SCL open;
  - pin 4 TIMEPULSE open;
  - pin 18 SAFEBOOT_N to TP131;
  - pin 13 LNA_EN to the Q127 gate;
  - pin 14 VCC_RF to the Q126 source.
- **Antenna supervisor:** Q126 drain → R207 → node GPS_ANT_SUP. That node goes to pin 5 EXTINT (ANT_SHORT_N),
  to C181 and to L5. L5 → GNSS_RF_ANT (J132 centre) → C182 → R209 (pi) → U17.11 RF_IN.
- **Radio U18:**
  - pin 1 VCC on 3V3;
  - pins 2, 7 and 16 to GND;
  - pin 6 ANT → RADIO_RF → J133 centre;
  - pins 4, 5, 8, 17 and 18 (DIO3) left unconnected.
- **Pins left unconnected:** U1.31 PA7 and U1.68/69 PA9/PA10 (bootloader USART1; add them to the NC list).
  The pyro sentinels U1.2/4/5/16/32 and U1.40 (PE10) stay unconnected.

### 5.4 Layout constraints that follow from the requirements

These are for the layout reviewer.

- U17/U18 on F.Cu, the SMAs on one short edge ≥ 12 mm apart, and GCPW on F.Cu over In1 GND (In1 is already a
  full GND pour).
- No signals under the modules on F.Cu or In1.
- Keep ≥ 5 mm from U2/L1 (3V3 buck, bottom, ≈ (18–27, 13–17)), U8/L3 (camera buck), U1 and U3 (QSPI), and
  stay clear of the pyro block.
- J1's wire entry faces +y, so a forward extension must move or rotate J1.
- An aft extension must shift or revise every absolute-coordinate contract (R7P1-17).
- Keep five supports: corners plus one in the middle third. (4, 46) still qualifies at 120 mm.

### 5.5 Pin and part contract to encode

- U17/U18/J132/J133 footprints and pin-net tuples (as §5.3).
- No radio, GPS or RF part pin on any PYRO*, ARM*, ACT_*, RAW_ACT or BAT_IN net: this is the hardware half of
  "radio commands can never arm or fire".
- PINNED codes: U17 C30005563 (or C4153167), U18 C5333985, L5, R207, Q126.

### 5.6 Checks, contracts and catalogs to update

**Board contracts**

- `tools/check_r6.py`:
  - drop J130/J131 from FOOTPRINTS and CONNECTORS (L24–29);
  - replace SIGNALS (L33–39) and the TLM/U14–U16/D130–D131/R192–R193 block (L283–301) with the §5.3 contract;
  - add 31, 68 and 69 to the NC list (L275);
  - change `110.01` to `120.01` and drop the 80–90 note (L309–311);
  - replace the J9/J130/J131 edge-block rule (L313–319) with "two SMAs on one short edge, ≥ 12 mm, RF keep-outs";
  - replace the J130/J131 legends (L391–392) with GPS/915 SMA legends.
- `m3_design/check_actuators.py`:
  - update the docstring (L2);
  - remove PINNED J130, J131, U14, U15, U16, R195, D130, D131 (L137–144);
  - delete L378–385, 389–395, 398–408 and 411–428;
  - keep IMU_INT1 (L386–388), R84 (L396–397), J9 (L409–410), J2 (L429–431) and the sentinels;
  - decide whether PE0 stays NC;
  - add the RF isolation rule and RF PINNED codes;
  - update DRU_SHA after review if RF rules go into `m3.kicad_dru`.
- `tools/fit_check.py`:
  - drop the two SH entries from MATED (L41–50), REQUIRED_MATED (L58) and the ref list (L325);
  - add an SMA plug + coax-bend envelope from the maker drawing and add its footprint to REQUIRED_MATED;
  - change 110.01 to 120.01 (L339–340);
  - drop `target_length_met` 80–90 (L349, 385);
  - RETENTION_HOLES are absolute (keep the origin, or move them).

**Cost and procurement gate**

- `tools/jlc_cost.py`: change the defaults and docstring to 126.41/52 (L2, 16, 51, 100–101).
- `tools/check_procurement.py`: change the targets dict, limits and message to 126.41/52 (L33–36, 68). Add the
  consignment allowance (R7P1-18).

**Tests**

- `test_procurement.py` L122;
- `test_fit_check.py` L81 (`'110 mm maximum'`) and L199–201 (J130 mate test → SMA);
- `test_r6_check.py` L207–208;
- `test_fab_validation.py` L104–110: its fixture uses C160393/J130, so re-target it to C161692/J9 or the SMA.

**Catalogs**

- `m3_design/procurement_catalog.json`:
  - remove selections C160390, C160393, C22984 and C728617;
  - delete the port refs from C11702, C1329837, C13612, C137691, C14663, C1671, C1849463, C21397, C2158003,
    C23024, C25744, C29936, C55266 and C85980;
  - add the eight new codes with stock snapshots and datasheet URLs;
  - update the U4 qualification (2026-10-15 recheck, ST eStore).
- `tools/verified_part_metadata.json`:
  - remove C160390, C160393, C22984 and C728617;
  - add C30005563 (U-BLOX, MAX-F10S-00B), C4153167 (if the fallback is to be ready), C5333985 (Chengdu Ebyte
    Elec Tech, E22-900MM22S), C841205 (MOLEX, "732511150" as JLC lists it; the maker form is 73251-1150,
    keep LCSC/Manufacturer/MPN consistent), C97998, C15127, C17903, C17168 and C1567.
- `tools/jlc_easyeda/pads.json` and `supplier_snapshot.json`: add EasyEDA pads for the new codes. Footprints
  exist: "GPS-SMD_MAX-F10S-00B", "SMD-18_L10.1-W9.7-P1.10-TL_SKG09F", "WIRELM-SMD_20P-L10.0-W10.0-P1.27-TL",
  "SMA-SMD_3734660". Number our SMA pads to match EasyEDA, or `jlc_orient` reports incomplete pad coverage.
  Removing C728617 is safe: the donor fallback for C21190/C861313 picks any verified R_0603_1608Metric entry,
  but re-run and check.
- `tools/jlc_corrections.json`:
  - regenerate with `jlc_orient.py`;
  - remove the keys "C160390|M3_SH_BM04B_SRSS_TB", "C160393|M3_SH_BM07B_SRSS_TB", "C22984|…" and "C728617|…";
  - drop the stale MECHANICAL entries for the SH footprints in `jlc_orient.py`.

**Fabrication outputs and generators**

- Fab outputs (`fab/`): regenerate BOM, CPL, Gerbers, assembly PDFs and manifest (`export_fab.py`), then
  `cost_check.json` and `stock_check.json` with the new targets; `schematic.net.xml` and `sheets/*.svg`.
- Generators: the `m3_design/r6_*.py` scripts recreate the ports. Do not re-run them on R7; use new r7_*
  scripts.

**Documents and firmware**

- REQUIREMENTS (§4); new M3_R7.md / R7_VALIDATION.md; STATUS, AGENTS, ORDERING and FMEA I-11/V-19.
- Parent VEHICLE stack row: length, SMA/coax allowance.
- Silkscreen revision legend.
- `m3_firmware`: new R7 binding (AGENTS §3); `pins_*.json` with the §5.3 map.

## 6. Stock (live JLCPCB, 5 boards, 2026-10-15)

### 6.1 Every current BOM line

"Need" is quantity × 5 or JLC's minimum, whichever is larger. ATP is `canPresaleNumber` (Inference, see header).

| LCSC | MPN | Refs | Qty/board | Need (5 boards) | JLC stock | ATP* | Lib | Unit $ | Status | After F10 |
|---|---|---|---:|---:|---:|---:|---|---:|---|---|
| C26633007 | LSM6DSV320XTR | U4 | 1 | 5 | 0 | -33 | expand | 11.2012 | **SHORT** | unchanged |
| C11702 | 0402WGF1001TCE | R9, R105, R127, R160, R192, R196–R202 | 12 | 60 | 14,390,831 | 11,282,749 | base | 0.0035 | ok | qty −8 (R192, R196–R202) |
| C12891 | CL31A226KAHNNNE | C89, C95 | 2 | 10 | 539,007 | 167,076 | base | 0.1236 | ok | unchanged |
| C131337 | B2B-PH-K-S(LF)(SN) | J123 | 1 | 5 | 342,422 | 328,711 | expand | 0.0354 | ok | unchanged |
| C1329837 | SRP5030T-6R8M | L3, L4 | 2 | 10 | 1,679 | 1,658 | expand | 1.1789 | ok | qty −1 (L4) |
| C13585 | CL31A106KBHNNNE | C80, C96 | 2 | 10 | 2,344,868 | 1,492,374 | base | 0.2720 | ok | unchanged |
| C13612 | SRV05-4.TCT | D121, D130, D131 | 3 | 15 | 69,551 | 68,329 | expand | 0.1626 | ok | qty −2 (D130, D131) |
| C137691 | RC0603FR-0766K5L | R85, R194 | 2 | 10 | 25,595 | 25,289 | expand | 0.0032 | ok | qty −1 (R194) |
| C14663 | CC0603KRX7R9BB104 | C71, C74, C83, C90, C93, C173, C175, C177, C179, C180 | 10 | 50 | 50,348,022 | 33,324,853 | base | 0.0163 | ok | qty −5 (C173, C175, C177, C179, C180) |
| C15639 | MS561101BA03-50 | U5 | 1 | 5 | 2,837 | 2,416 | expand | 6.7240 | ok | unchanged |
| C15849 | CL10A105KB8NNNC | C22 | 1 | 5 | 9,792,088 | 7,288,771 | base | 0.0141 | ok | unchanged |
| C160390 | BM04B-SRSS-TB(LF)(SN) | J131 | 1 | 5 | 39,825 | 35,736 | expand | 0.2537 | ok | removed (code dropped) |
| C160393 | BM07B-SRSS-TB(LF)(SN) | J130 | 1 | 5 | 28,647 | 27,294 | expand | 0.3724 | ok | removed (code dropped) |
| C161115 | GCJ188R71H104KA12D | C128 | 1 | 5 | 70,633 | 64,070 | expand | 0.0552 | ok | unchanged |
| C161692 | BM04B-GHS-TBT(LF)(SN) | J9 | 1 | 5 | 1,188 | 878 | expand | 0.3935 | ok | unchanged |
| C1623 | CL10B474KA8NNNC | C85 | 1 | 5 | 810,600 | 622,359 | base | 0.0297 | ok | unchanged |
| C165948 | TYPE-C-31-M-12 | J3 | 1 | 5 | 379,979 | 365,727 | expand | 0.1862 | ok | unchanged |
| C1671 | CL10C470JB8NNNC | C77, C174 | 2 | 10 | 502,579 | 357,087 | base | 0.0064 | ok | qty −1 (C174) |
| C17513 | 0805W8F1001T5E | R150–R153 | 4 | 20 | 44,558,401 | 42,830,819 | base | 0.0035 | ok | unchanged |
| C17557 | 0805W8F2200T5E | R32, R33, R126, R162 | 4 | 20 | 764,491 | 631,815 | base | 0.0054 | ok | unchanged |
| C178373 | 35SVPK330M | C84 | 1 | 5 | 1,772 | 1,671 | expand | 1.7218 | ok | unchanged |
| C1848 | CL31B105KBHNNNE | C91 | 1 | 5 | 423,530 | 261,981 | base | 0.0682 | ok | unchanged |
| C1849463 | TPS259570DSGR | U7, U16 | 2 | 10 | 4,657 | 4,480 | expand | 0.6685 | ok | qty −1 (U16) |
| C191023 | 1N5819WS | D123 | 1 | 5 | 4,312,407 | 4,059,463 | base | 0.0138 | ok | unchanged |
| C19666 | CL10A475KO8NNNC | C23, C28 | 2 | 10 | 3,653,508 | 2,923,800 | base | 0.0203 | ok | unchanged |
| C1985619 | NX3225GA-25.000M-STD-CRG-2 | Y1 | 1 | 5 | 5,497 | 5,254 | expand | 0.3891 | ok | unchanged |
| C20917 | AO3400A | Q122, Q123 | 2 | 10 | 751,380 | 596,907 | base | 0.0891 | ok | +1 (Q127) |
| C21120 | CL10B224KA8NNNC | C126 | 1 | 5 | 1,209,601 | 1,047,091 | base | 0.0086 | ok | unchanged |
| C21190 | 0603WAF1001T5E | R74, R77, R100, R101, R103, R110 | 6 | 30 | 24,118,513 | 17,751,971 | base | 0.0019 | ok | unchanged |
| C21397 | GRM32ER71E226KE15L | C72, C73, C75, C76, C82, C92, C170–C172 | 9 | 45 | 80,197 | 69,799 | expand | 0.3147 | ok | qty −3 (C170–C172) |
| C2158003 | AP63301WU-7 | U8, U14 | 2 | 10 | 11,802 | 11,601 | expand | 0.8071 | ok | qty −1 (U14) |
| C22939 | 0603WAF220KT5E | R164 | 1 | 5 | 163,610 | 76,530 | base | 0.0033 | ok | unchanged |
| C2296 | KT-0805Y | LED2 | 1 | 5 | 790,123 | 727,208 | base | 0.0146 | ok | unchanged |
| C22984 | 0603WAF3002T5E | R191 | 1 | 5 | 1,628,349 | 1,361,056 | base | 0.0050 | ok | removed (code dropped) |
| C23024 | 0603WAF3003T5E | R81, R190, R206 | 3 | 15 | 593,147 | 502,645 | base | 0.0042 | ok | qty −2 (R190, R206) |
| C23178 | 0603WAF4703T5E | R80, R165 | 2 | 10 | 1,309,065 | 1,175,634 | base | 0.0030 | ok | unchanged |
| C23630 | CL10A225KO8NNNC | C19, C20, C87, C120 | 4 | 20 | 3,530,007 | 2,956,809 | base | 0.0133 | ok | unchanged |
| C25468 | 25121WF330LT4E | R166 | 1 | 5 | 48,874 | 44,508 | expand | 0.0395 | ok | unchanged |
| C25741 | 0402WGF1003TCE | R60, R120, R122, R123 | 4 | 20 | 9,728,783 | 8,054,081 | base | 0.0016 | ok | +1 (R208) |
| C25744 | 0402WGF1002TCE | R5, R10, R11, R61–R64, R104, R121, R128, R131, R154–R157, R161, R163, R193, R203–R205 | 21 | 105 | 21,997,835 | 16,879,593 | base | 0.0016 | ok | qty −4 (R193, R203–R205), +2 (R210, R211) |
| C25804 | 0603WAF1002T5E | R75, R76, R78, R88–R92, R102, R167 | 10 | 50 | 32,287,026 | 22,481,309 | base | 0.0052 | ok | unchanged |
| C25819 | 0603WAF4702T5E | R87 | 1 | 5 | 1,964,711 | 1,305,880 | base | 0.0021 | ok | unchanged |
| C25900 | 0402WGF4701TCE | R12, R13, R168, R170, R172 | 5 | 25 | 16,121,415 | 14,281,591 | base | 0.0023 | ok | unchanged |
| C25905 | 0402WGF5101TCE | R7, R8, R124, R129, R132, R173, R175, R177 | 8 | 40 | 5,299,051 | 4,472,148 | base | 0.0024 | ok | unchanged |
| C2760089 | AON6403 | Q120, Q121 | 2 | 10 | 1,521 | 1,509 | expand | 0.7256 | ok | unchanged |
| C2915641 | DB128V-5.08-4P-GN-S | J1 | 1 | 5 | 78,175 | 77,008 | expand | 0.4194 | ok | unchanged |
| C29936 | CL10B105KA8NNNC | C86, C97, C98, C176 | 4 | 20 | 208,019 | 37,778 | expand | 0.0204 | ok | qty −1 (C176) |
| C3013496 | CRM2512-FX-2R00ELF | R134 | 1 | 5 | 2,895 | 2,813 | expand | 0.5544 | ok | unchanged |
| C307331 | CL05B104KB54PNC | C5, C13–C18, C21, C24, C29–C32, C88, C99, C100, C160 | 17 | 85 | 25,003,819 | 21,257,037 | base | 0.0099 | ok | +2 (C183, C184) |
| C32713291 | HX PZ2.54-3x4P ZZ | J122 | 1 | 5 | 27,862 | 27,461 | expand | 0.1872 | ok | unchanged |
| C32949 | CL05C100JB5NNNC | C25, C26 | 2 | 10 | 2,216,164 | 1,899,608 | base | 0.0057 | ok | unchanged |
| C3662793 | TPS259470LRPWR | U9 | 1 | 5 | 328 | 284 | expand | 1.4463 | ok | unchanged |
| C4109 | 0402WGF2001TCE | R125, R130, R133, R178, R180, R182 | 6 | 30 | 7,745,244 | 7,188,015 | base | 0.0026 | ok | unchanged |
| C4241878 | MCT0603MD2004BP500 | R82 | 1 | 5 | 2,294 | 200 | expand | 0.0997 | ok | unchanged |
| C430601 | DB128L-5.08-2P-BK-S | J121, J124 | 2 | 10 | 24,404 | 24,237 | expand | 0.2053 | ok | unchanged |
| C431195 | AON7524 | Q124 | 1 | 5 | 17,570 | 17,519 | expand | 0.3832 | ok | unchanged |
| C45783 | CL21A226MAQNNNE | C6–C11, C150, C151 | 8 | 40 | 3,886,218 | 2,989,321 | base | 0.1924 | ok | +1 (C185) |
| C46550466 | MA25V470M8x10 | C121 | 1 | 5 | 123,825 | 123,127 | expand | 0.2800 | ok | unchanged |
| C47546 | BAT54S,215 | D122 | 1 | 5 | 172,136 | 169,737 | expand | 0.0287 | ok | unchanged |
| C485916 | TPS2121RUXR | U11 | 1 | 5 | 28,449 | 28,031 | expand | 0.9147 | ok | unchanged |
| C5186957 | TXU0202DCUR | U12 | 1 | 5 | 18,062 | 15,901 | expand | 0.8577 | ok | unchanged |
| C5271084 | STM32H743VIT6TR | U1 | 1 | 5 | 1,490 | 1,423 | expand | 12.5300 | ok | unchanged |
| C55266 | TPS2553DBVR | U10, U15 | 2 | 10 | 54,186 | 53,169 | expand | 0.4468 | ok | qty −1 (U15) |
| C57112 | 0603B103K500NT | C60, C94, C122, C127, C129 | 5 | 25 | 5,941,585 | 4,452,299 | base | 0.0102 | ok | +1 (C181) |
| C57269 | SWPA4030S4R7MT | L1 | 1 | 5 | 23,943 | 23,072 | expand | 0.0610 | ok | unchanged |
| C705755 | RT0603BRD07280KL | R83 | 1 | 5 | 6,721 | 6,710 | expand | 0.0563 | ok | unchanged |
| C728617 | RT0603DRD074K42L | R195 | 1 | 5 | 4,637 | 4,411 | expand | 0.0152 | ok | removed (code dropped) |
| C7519 | USBLC6-2SC6 | D4 | 1 | 5 | 48,201 | 43,171 | expand | 0.1772 | ok | unchanged |
| C780769 | AP63203WU-7 | U2 | 1 | 5 | 4,191 | 322 | expand | 1.1821 | ok | unchanged |
| C83849 | SMBJ12CA | D8 | 1 | 5 | 22,305 | 21,552 | expand | 0.1241 | ok | unchanged |
| C84256 | NCD0805R1 | LED1 | 1 | 5 | 3,972,331 | 3,637,555 | base | 0.0134 | ok | unchanged |
| C85098 | B340A-13-F | D9 | 1 | 5 | 28,458 | 26,151 | expand | 0.0832 | ok | unchanged |
| C8591 | BAT54A | D120 | 1 | 5 | 54,507 | 54,441 | expand | 0.0243 | ok | unchanged |
| C85980 | GRM1885C1H472JA01D | C70, C81, C178 | 3 | 15 | 76,248 | 68,579 | expand | 0.0212 | ok | qty −1 (C178) |
| C861162 | RT0603BRD07172KL | R71 | 1 | 5 | 4,425 | 4,424 | expand | 0.0543 | ok | unchanged |
| C861207 | RT0603BRD071K78L | R70 | 1 | 5 | 5,081 | 5,077 | expand | 0.0374 | ok | unchanged |
| C861313 | RT0603BRD0730K9L | R72 | 1 | 5 | 2,666 | 2,647 | expand | 0.0437 | ok | unchanged |
| C861551 | RT0603BRD07750RL | R84 | 1 | 5 | 2,661 | 1,559 | expand | 0.0348 | ok | unchanged |
| C861568 | RT0603BRD0780K6L | R86 | 1 | 5 | 5,945 | 5,918 | expand | 0.0411 | ok | unchanged |
| C89347 | TPS70933DBVR | U13 | 1 | 5 | 45,375 | 43,939 | expand | 0.3374 | ok | unchanged |
| C94598 | MLT-5020 | LS120 | 1 | 5 | 89,296 | 86,287 | expand | 0.4403 | ok | unchanged |
| C97521 | W25Q128JVSIQ | U3 | 1 | 5 | 66,926 | 49,561 | base | 2.5598 | ok | unchanged |

Result: 81 of 82 lines are in stock with at least twice the need. U4 is short.

### 6.2 New and candidate parts

| Part | LCSC | Stock | ATP* | Need | Min | $ at need | Lib | Status |
|---|---|---:|---:|---:|---:|---:|---|---|
| MAX-F10S-00B | C30005563 | 18 | 9 | 5 | 1 | 19.7692 | expand | OK, thin; reserve |
| MAX-M10S-00B (fallback) | C4153167 | 1,136 | 1,050 | 5 | 1 | 10.8360 | expand | OK |
| E22-900MM22S | C5333985 | 462 | 420 | 5 | 1 | 6.5120 | expand | OK |
| E22-900M22S (layout alternate) | C411293 | 32 | −73 | 5 | 2 | 6.9343 | expand | Oversubscribed (Inference) |
| Cinch/Bel 142-0701-801 SMA | C3173345 | 2 | 1 | 10 | 1 | 8.9039 | expand | **SHORT** |
| Molex 73251-1150 SMA | C841205 | 211 | 198 | 10 | 1 | 3.8935 | expand | OK (recommended) |
| XUNPU SMA-KE-347-H13.5-1.6 | C5723200 | 1,498 | 1,099 | 10 | 1 | 0.4126 | expand | OK (low-cost; datasheet image-only, unverified) |
| BAT WIRELESS BWSMA-KE-P001 | C496550 | 73,004 | 71,535 | 10 | 1 | 0.3180 | expand | OK (unverified) |
| LQG15HS47NJ02D 47 nH | C97998 | 24,540 | 23,754 | 5 | 1 | 0.0245 | expand | OK |
| LQG15HS27NJ02D 27 nH (M10S fallback) | C12669 | 122,612 | — | 5 | 1 | 0.0190 | expand | OK |
| AO3401A | C15127 | 578,780 | 448,341 | 5 | 1 | 0.1020 | base | OK |
| Si1016X-T1-GE3 (u-blox T1/T2) | C142570 | 0 | 0 | 5 | 25 | 0.3718 | expand | **SHORT** |
| SI1016X-TP (TECH PUBLIC) | C50314620 | 2,775 | 2,775 | 5 | 1 | 0.0822 | expand | OK (pinout unverified) |
| 1206W4F100JT5E 10 Ω 0.25 W | C17903 | 1,107,274 | 883,633 | 5 | 1 | 0.0059 | base | OK |
| 0402WGF0000TCE 0 Ω | C17168 | 9,266,026 | 7,184,378 | 5 | 1 | 0.0012 | base | OK |
| 0402CG470J500NT 47 pF C0G | C1567 | 558,404 | 458,741 | 5 | 1 | 0.0081 | base | OK |

### 6.3 U4 options (ranges kept at ±16 g / ±320 g / ±4000 dps)

1. **Consignment from a franchised source, recommended.**
   - ST eStore lists LSM6DSV320XTR "In stock": $10.06 (1–4), $8.48 (5–9), $7.88 (10–24), fetched 2026-10-15.
     The page warns of high order volume.
   - Cached search results (not live) showed Farnell UK 69 units and Digi-Key 0 with a 24-week lead time.
     Re-check before buying.
   - Mark U4 as consigned in the CAD field `JLC_Assembly`; `export_fab.py` supports it.
   - Add the consignment allowance to the stock gate.
2. **JLC parts pre-order or Global Sourcing of C26633007.** Stock 0 with ATP −33 suggests a backlog
   (Inference). Lead time is unknown.
3. **No in-stock pin- and footprint-compatible alternative keeps the ranges.** Not proposed:
   LSM6DSV80X (±80 g, stock 0), ISM6HG256X (±256 g, stock 1), LSM6DSV32X (±32 g).

## 7. Cost estimate

Method: as in `tools/jlc_cost.py`. Unit price is taken at the break covering quantity × 5 boards, with a $1.53
Standard PCBA feeder fee per unique code ÷ 5. Data are the live JLC responses above. The baseline was reproduced
with `jlc_cost.py` itself.

| Step | Parts $/board | Codes | Extended | Total $/board |
|---|---:|---:|---:|---:|
| Current R6 BOM | 59.31 | 82 | 48 | **84.40** |
| Remove port parts (§5.1) | 54.76 | 78 | 45 | 78.63 (−5.77) |
| Add recommended RF parts (§5.2) | 89.29 | 86 | 49 | **115.60** (+36.97) |

- **Net delta against R6: +$31.20/board.** The M3 cap is $126.41 with ≤ 52 extended codes, leaving $10.81 and
  3 codes of margin. JLC minimum purchases add nothing.
- **Largest additions:** MAX-F10S $19.77, E22-900MM22S $6.51, two Molex SMAs $7.79, 8 new codes $2.45 in
  feeder fees. The bias, supervisor and pi parts cost $0.24.
- **Variants:**
  - XUNPU SMA: $108.64 (49 extended);
  - SI1016X-TP instead of AO3401A/AO3400A: $115.49 (50 extended);
  - MAX-M10S fallback: $106.67;
  - E22-900M22S: $116.03.
- **Not included:**
  - fixed two-sided fees of $83.96/order plus a possible $14.93 handling fee;
  - manual-solder joints for the SMA straddle legs;
  - impedance-control or stackup surcharges;
  - U4 consignment logistics (ST price $8.48 against JLC's $11.20 list, i.e. −$2.72/board before JLC's
    consignment charges).
- Prices change daily. Re-run `jlc_cost.py`/`jlc_stock.py` on the regenerated R7 BOM right before ordering.

## 8. Sources

- JLCPCB component API, `https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList` (queried 2026-10-15T20:20–20:38Z); EasyEDA footprints `https://easyeda.com/api/products/<code>/svgs`.
- u-blox MAX-F10S data sheet UBXDOC-963802114-12732 R03: https://content.u-blox.com/sites/default/files/documents/MAX-F10S_DataSheet_UBXDOC-963802114-12732.pdf
- u-blox MAX-F10S integration manual UBXDOC-963802114-12892 R01: https://content.u-blox.com/sites/default/files/documents/MAX-F10S_IntegrationManual_UBXDOC-963802114-12892.pdf
- u-blox MAX-M10S data sheet UBX-20035208 R03 (LCSC copy): https://www.lcsc.com/datasheet/lcsc_datasheet_2411220051_U-BLOX-MAX-M10S-00B_C4153167.pdf
- u-blox MAX-M10S integration manual UBX-20053088 R01: https://cdn.sparkfun.com/assets/5/c/a/0/b/MAX-M10S_IntegrationManual_UBX-20053088.pdf
- EBYTE E22-900MM22S user manual v1.3 (LCSC): https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2212192008_Chengdu-Ebyte-Elec-Tech-E22-900MM22S_C5333985.pdf
- STMicroelectronics STM32_open_pin_data, STM32H743VITx.xml: https://github.com/STMicroelectronics/STM32_open_pin_data/blob/master/mcu/STM32H743VITx.xml
- ST eStore LSM6DSV320XTR: https://estore.st.com/en/lsm6dsv320xtr-cpn.html ; LCSC C26633007: https://www.lcsc.com/product-detail/C26633007.html
- Molex 73251-1150 (element14 listing, SMA jack, 50 Ω, PCB edge mount): https://sg.element14.com/molex/73251-1150/rf-coax-conn-sma-jack-50-ohm-pcb/dp/1909295 ; drawing (not retrieved, site timed out): https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/732/73251/732511150_sd.pdf
- Diodes AP63203 (2 A, 3.3 V; LCSC page): https://www.lcsc.com/datasheet/lcsc_datasheet_2201131130_Diodes-Incorporated-AP63203WU-7_C780769.pdf
- Jiangsu Huaneng MLT-5020 (LCSC): https://www.lcsc.com/datasheet/lcsc_datasheet_2108131530_Jiangsu-Huaneng-Elec-MLT-5020_C94598.pdf
- Repository records: docs/ROCKET_FC_FROZEN_DESIGN.md §3.7/§3.10 (bootloader pin reservations, AN2606 Table 113, not re-read here); docs/FMEA_REDUNDANCY.md; docs/ORDERING.md; `reports/Compact rocket GPS and radio.md`.
