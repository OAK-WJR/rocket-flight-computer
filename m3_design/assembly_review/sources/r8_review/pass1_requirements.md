# R8 review pass 1: requirements traceability

Reviewer dimension: requirements traceability. I checked every REQUIREMENTS row (F1–F10, P1–P3, M1–M3, R8 acceptance)
against the CAD, the gate and the records. I also checked the R8 pin contract against F10 and R8_DECISIONS, the
consistency of REQUIREMENTS, STATUS, ORDERING, MARGIN_PRESCRIPTION, AGENTS, M3_R8 and R8_VALIDATION, and whether the
R8 deviation list is complete and honest.

- **Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `429b6db4dc95c1a0fd3e736625c416c20fa0e7fc72f6f6c9c576003340dc1987`. I checked the hash before and after my runs.
- **Read-only:** no repository file changed except this report. The board was never saved. The R7 comparison board
  came from `git show 431025d:…` into the session scratchpad and was deleted afterwards.
- **Labels:** Inference marks anything not measured and not taken from a maker document.

**Result: 0 Critical, 1 Major, 9 Minor.**

## 1. What I ran

| Run | Result |
|---|---|
| `tools/check.sh` (KiCad 10.0.6) | **exit 0**: DRC 0, unconnected 0, parity 0, ERC 0; audit OK; silk in outline; `check_r8` OK; route_check r8 0 failing / 3 allowlisted / 0 leftovers; `check_actuators` OK; `fit_check` OK (J9 mated 0.03, C84 1.37 mm, R12.1 4.452 mm from (4, 64)) |
| `check_r8` evidence (from the gate's report) | rigid 12/12; U1 map 100/100; loader pins per D5; F10 separation 5.94 mm (R306–U1), fast line 5.075 mm (R306–USB_DM); fence 25 vias, openings 2.015 / 2.60 / 2.10 / 2.05 mm; RF gaps 3.90 / 2.65 / 1.55 / 1.55 mm; D18 2.65 mm; D19 none; In2 signal = only the rigid 3.4 mm link |
| `route_check --profile r8 --bumps-all --routes` | 0 failing. `local_bump_review` gives 1 instance: BAT_ENABLE F.Cu, 32.93 → 25.73 mm. It is a **false positive**: the run feeds TP84.1 and C87.1 by passing through them |
| Netlist diff, R7 `431025d` against R8 | exactly 28 changes: 27 U1 pins and R310.1 3V3_RADIO → 3V3. No component, value, footprint or field change |
| `fab_manifest.verify_manifest` | OK, 5 outputs, board `429b6db4…` |
| `jlc_orient --verify-cpl` | 85 top + 126 bottom rows rebuilt, worst 0.491 mm, 8 placement-only, 219 rows |
| `cost_check.json` / `stock_check.json` | $106.00, 52 extended, `checked_utc 2026-10-19T23:51:04Z`; short: U4 only |
| My scans (pcbnew; method in Appendix A) | part sides 89 F / 130 B; 81 hidden designators (= M3_R8 list); M3_R8 placement table 37/37 exact; silk text ≥ 1.0 mm, lines ≥ 0.15 mm; no via or fill under U4 / U5 bodies; chain detours, adjacency, via-copper steps and poured-net hops (findings 01, 04) |
| Maker documents (local copies) | DS12110 Rev 11; RM0433 Rev 9 §50.11.4 and Table 426 (IOSWP); AN2606 Rev 70 Table 2 (p. 35) and Table 135 (pp. 320–323) |

## 2. Closure of the previous pass in this dimension

There has been no R8 review pass before this one. The last pass in this dimension was R7 review pass 8
(`sources/r7_review/pass8_docs.md`, 0 Critical / 0 Major / 3 Minor, recorded and not reworked under the owner's R7
acceptance). How each item stands on R8:

| R7 pass-8 ID | Item | On R8 |
|---|---|---|
| P8-DOCS-01 | C15 adjacency list incomplete | **Not closed, and wider now.** R8_VALIDATION has no adjacency row at all. R8's new copper has 32 net pairs at 0.150–0.198 mm. This is part of R8P1-REQUIREMENTS-01 |
| P8-DOCS-02 | inexact figures; via-field currents not stated | Figures: new residues, R8P1-REQUIREMENTS-05. Via fields: MARGIN_PRESCRIPTION's R8 note now says "not assessed for current" (R8P1-REQUIREMENTS-10) |
| P8-DOCS-03 | `legend_subjects` measures part-level box gaps, so legends can read across neighbours | **Not closed.** The tool is unchanged, terminal pin legends are not checked against their pins, and J1's pin legends now read across (R8P1-REQUIREMENTS-03) |

## 3. Requirement walk on `429b6db4…`

Verdicts: **Pass** (shown in the CAD, gate or fab files), **Partial** (the CAD part passes, the rest is open), **NV**
(needs the bench, flight or firmware).

| Row | Verdict | Evidence / remark |
|---|---|---|
| Sources (one CH1, isolated Blue Jay, 4 servos, on-board MAX-F10S / E22, the uplink cannot arm) | Pass | `check_actuators` byte-identical and OK; no PYRO2 / ARM2 net (`check_r8`); no RF-part pin on a SAFETY_NETS net |
| F1–F3, F5 | Pass (parts) | Circuit unchanged (netlist diff). U4 stays bottom, rotation 0 (axes as M3_R5 §3); the lever arm is x −13.0 mm (D77) |
| F4 | Partial | The R8 solve (M3_R8) is within D12. Via-field currents are not assessed (finding 10). Stall test: NV |
| F6 | Pass (CAD), NV | Servo pins, pull-downs, C24 100 nF, C87 / R81 unchanged. Bootloader statement: finding 02 |
| F7 | Pass (CAD), NV | RAW_ACT → J124.2 0.44 mΩ (M3_R8) |
| F8 | Pass (CAD), legend residue, NV | DRC 0 under the unchanged `m3.kicad_dru`. ARM / IGN / BAT / CAM / GNSS / RADIO legends are present. J1 pin legends: finding 03. BAT_ENABLE crossing the block: finding 04 |
| F9 | Pass (CAD), NV | Protection parts 3.86–10.6 mm from J1.1 (the records say 4.6; finding 05). Hot-plug at U9 IN is an Inference, with the bench test listed |
| F10 | Pass (CAD), NV | Pin contract verified (section 4). Strip rigid; per-layer nets and fence by `check_r8`. Bootloader wording: finding 02 |
| P1 | Pass | 46 × 118 mm; parent VEHICLE row still names R7 (D84, proposed, not applied; R7 is the orderable revision) |
| P2 | Pass (CAD) | Five supports; nearest bottom pad 4.452 mm; tie path 2.2 mm. f1 −13 % on R6 (C10). The P2 premise text is stale (finding 09) |
| P3 | Pass (procedure) | No via or fill under U4 / U5 bodies; coating list unchanged; staking updated |
| M1 | Pass, except U4 stock | Stock short U4 only. CPL verified. M1-named reflow-limited parts did not change side (C84, C121, LS120, U30, U31 top; U5 bottom) |
| M2 (JLC rules, via-in-pad, silk) | Pass | DRC 0; `check_r8` via-in-SMD-pad OK; J2 nearest via 0.915 mm from a pad centre (measured) |
| M2 (clean routing, deviation list) | **Not met: list incomplete** | Finding 01. Owner acceptance is open in any case |
| M3 | Pass | $106.00, 52 / 52, 23:51Z, bound to BOM `be711876…`; rerun within 24 h of ordering |
| R8 acceptance | Not met (as recorded) | Review loop, owner acceptance, U4 consignment, 24 h cost run. The records' ordering gate wording is inconsistent (finding 06) |

## 4. R8 pin contract against F10 and the decisions

- **Board, netlist and table agree.** The pad nets of U1, U30, U31, R305–R316, FB30 / FB31 and TP30 match
  `pin_table.tsv`, F10 and the schematic notes.
  - The netlist diff against R7 is exactly D2 / D3 / D4's 28 changes.
- **F10 items, each confirmed on the board:**

  | Item | Board |
  |---|---|
  | GNSS UART | USART6 PC6 / PC7 with R306 / R305 220 Ω |
  | GNSS reset | RESET_N on PD14 only (no pull, no capacitor) |
  | TIMEPULSE | R307 1 kΩ to PD15 (TIM4_CH4, AF2) |
  | SAFEBOOT_N | on TP30 |
  | U30 V_BCKP / VIO_SEL | unconnected |
  | Radio SPI | SPI2: PB10 SCK, PB11 NSS (R310 100 kΩ to 3V3), PB14 / PB15 with IOSWP |
  | Radio control | BUSY PD8; NRST PE9 with R311 2 kΩ to GND; DIO1 PE15; RXEN PD9 with R312 100 kΩ |
  | TXEN | U31.9 tied to U31.19 (DIO2) |

- **IOSWP:** RM0433 Rev 9 §50.11.4 bit 15 ("Original MISO pin becomes MOSI…") and Table 426 confirm D2.
- **Loader map:** AN2606 Rev 70 Table 135 confirms D2, D3 and D5's map, including these entries:

  | Pins | Bootloader use |
  |---|---|
  | PB14 / PB15 | USART1 (PB14 push-pull output) |
  | PB10 / PB11 | USART3 (PB10 input until detected on 0x91) |
  | PA4–PA7 | SPI1 slave |
  | PE11–PE14 | SPI4 slave |
  | PB6 / PB9 | I2C1 open drain |

  PC13, PD5, PD7, PC8, PE7–PE9, PE15, PD9, PD14 and PD15 are not loader pins.
- **EXTI map (D6):** one port per line. Lines 5 / 6 / 8 share EXTI9_5 and lines 11 / 14 / 15 share EXTI15_10. BUSY is
  polled and TIMEPULSE is captured.
- **One gap, finding 02.** BOOT0 is tied low (R5 10 kΩ) and is not on J2, so AN2606 Pattern 10 (BOOT0 = 1) is
  unreachable. The ROM bootloader can be entered only by the firmware jump that ORDERING §5 names. F10's "held low …
  in the ROM bootloader" is therefore a firmware duty, not a hardware property.
- **PC13 (BUZZ_DRV) drive:** checked against DS12110 Rev 11.
  - The H743 datasheet gives only the 2 MHz limit (Table 52 note 2) and the 3 mA VOH test condition for PC13–PC15. It
    has no "not a current source / 30 pF" note.
  - The AO3400A gate behind 220 Ω is therefore not a datasheet violation. No finding.

## 5. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R8P1-REQUIREMENTS-01 | **Major** | REQUIREMENTS M2 (l.75): "What review checks: … whole-run detours on nets without a pour … adjacency on every net …"; "every review-only residual is listed, with location, rule, measured reason …" | **The R8 deviation list leaves out whole M2 review categories that R7's list carried. Accepting it would leave unlisted M2 deviations.** Part C (R8_VALIDATION l.136–149) has 10 rows and no row, and no "swept, none found" statement, for chain (whole-run) detours on nets without a pour (R7 C24 / C25), adjacency (R7 C3 / C4 / C15) or extra vias on non-critical nets. No R8 record says the sweep was run (`grep` of M3_R8, R8_VALIDATION and r8_design/*.md: no `--bumps-all`, chain-detour or adjacency sweep). | (a) **Chain detours on nets without a pour:** 27 runs on R8 meet M2's chain criterion (run between nodes > 1.25 × octile and > 0.5 mm longer). 20 are on critical nets, including PYRO1_CONT B.Cu 45.43 mm against 36.18 mm (28.4, 88.61)–(23.17, 54.6), USB_LIMITED 27.30 / 21.12, RAW_PROTECTED 47.09 / 35.32, SPI1_SCK 16.39 / 13.11, QSPI_CLK 6.23 / 4.59 and USB_DM 3.36 / 1.00. 7 are on non-critical nets. Full table in Appendix B. **The same scan on R7 `c872a3d3…` gives exactly 38 = C24 (21) + C25 (17)**, so the metric is R7's. Only RADIO_TXEN (C5) and a few u_turn / extra_bends information rows touch these runs, and none gives a run-level reason. (b) **Adjacency:** 32 net pairs at 0.150–0.198 mm edge to edge (R7 C15's bar is 0.2 mm), 30 of them in R8-new copper (Appendix B). Examples: SPI1_SCK B.Cu 0.150 mm from the IMU_CS and SPI1_MOSI vias (10.5 / 9.5, 55.65); SERVO1_MCU 0.150 mm from the VLOGIC via (26.95, 60.5); RADIO_NRST 0.150 mm from the CAM_MCU_RX via (33.9, 44.0); I2C1_SCL / SDA 0.154 mm; VBUS_SENSE via 0.190 mm from USB_DM. (c) **Extra vias on non-critical nets** (`--routes`): BAT_ENABLE 2 (needs 1), NRST 2 (needs 1), CAM_MCU_RX 2 (needs 0; only its hop is in E). (d) For contrast, the other review categories came out clean in my scans: steps inside via copper (only the rigid ARM1_SENSE (18.18, 91.3)); poured-net hops (one, 3V3 F.Cu (34.4, 69.65)–(34.4, 73.2), needed to cross SERVO4_MCU and In2 GND); non-critical local bumps (one false positive) | Run the review sweep on `429b6db4…` and add part-C rows: chain detours on nets without a pour (each run with location and a measured reason, or removed), adjacencies under 0.2 mm (or widen the signal-to-signal ones: SPI1_SCK / IMU_CS / MOSI vias, SERVO1_MCU / VLOGIC via, RADIO_NRST / CAM_MCU_RX via, CAM_FAULT_N / CAM_PWR_EN, BUZZ_DRV / PULLPIN), and non-critical extra vias. Give an explicit "swept, none" line per M2 review category. Re-count the owner summary |
| R8P1-REQUIREMENTS-02 | Minor | F10 (l.60): NRST "held low by a pull-down whenever the MCU is in reset or in the ROM bootloader, so the radio cannot transmit"; D2 / D6; binding note | **Bootloader entry on this board is only by firmware jump, so "radio held in reset in the bootloader" depends on firmware.** BOOT0 (U1.94) has only R5 10 kΩ to GND and is not on J2 (J2.6 NC). AN2606 Rev 70 Table 2 (p. 35) Pattern 10 needs BOOT0 = 1, so the ROM bootloader is reachable only by the firmware jump to DFU (ORDERING §5) or by an option-byte change. After a jump, PE9 keeps whatever the application last drove (Inference: the bootloader configures only Table 135's pins). The loader-capture safety of D2 / D5 still holds without the radio in reset (NSS is high through R310 plus the loader pull-up). The "cannot transmit" property does not. | U1.94 nets: BOOT0 = U1.94, R5.1 only; J2 pin 6 `unconnected`; AN2606 Table 2 / Table 135; D6 constraints 1–7 and `r8_binding_note.json` have no jump rule | Add binding constraint 8 (D6, binding note, F10 wording): before jumping to the system bootloader, put the SX1262 in sleep, drive PE9 low and return it to analog (or reset GPIOE). F10: "in reset, or in the ROM bootloader entered after that preparation" |
| R8P1-REQUIREMENTS-03 | Minor | F8 (l.58): "… with unambiguous pin legends"; R7 P8-DOCS-03 | **R8's J1 pin legends read across neighbouring pins and parts (R7's sat over their own pins).** "2:GND" box x 21.49–23.19, y 100.24–104.96 lies 5.53 mm from J1.3 (SW) and 5.92 mm from J1.2 (GND). "4:SW" box x 10.83–12.53 lies 5.42 mm from **J124.1 (PYRO1_BUS, the ARM terminal)** and 6.12 mm from J1.4. R7: "2:GND" x 25.69–27.39 over J1.2 (5.44 mm), "4:SW" x 14.53–16.23 over J1.4. Also "2:RAW" moved from 3.86 to 6.21 mm from J124.2, and "2:E1+" from 2.31 to 3.88 mm from J121.2. `pin_legends` checks only J9, J2 and the SMA words, and `legend_subjects` is part-level, so the gate cannot see this. A wrong J1 wire is benign by F9's design (Inference), but F8's legend rule exists for terminal identification | pcbnew text bounding boxes against pad centres on both boards (J1 pins x 30.62 / 25.54 / 20.46 / 15.38, y 110.4); render `r8_top.png` | In `r8_post.py`, put "4:SW" and "2:GND" in the forward-edge strip beside "3:SW" (y ≈ 116–117.6, centred on x 15.38 and 25.54; this fits with ≥ 0.85 mm between texts), or over their pins as R7 had them. Add a terminal pin-legend proximity test (nearest pin = own pin) |
| R8P1-REQUIREMENTS-04 | Minor | M3_R8 accuracy (l.242–243: "No signal net now passes the block"); pyro-block neighbour analysis | **BAT_ENABLE (U9's EN / UVLO, a megohm node) now crosses the PYRO_BLOCK area for 25.5 mm.** It runs F.Cu y 98.45, x 17.4–42.9, 0.70 mm from both R134 pads (PYRO1_IGN and PYRO1_BUS). In R7 it stayed near U9 at y 37–41. The records list BAT_ENABLE as a 0.70 mm neighbour but say no signal net passes the block, and they do not assess it. **Inference:** a leak ≤ about 1.7–2.0 MΩ from armed bus copper to EN (against R81 300 kΩ, EN about 1.1–1.2 V) would hold U9 on with the switch open while armed. That matters if the switch is the pad arming device (F8, FMEA H-6(b)). The exposure is not new in kind: BAT_IN copper already neighbours R165 / BAT_ENABLE in the band, and the track is under mask in the coated block | `netgap.py`: BAT_ENABLE vs PYRO1_IGN 0.70 mm (track–R134.1), vs PYRO1_BUS 0.70 mm (R134.2), vs PYRO1_OUT 2.72 mm (R81.1–J121.1, bottom). BAT_ENABLE copper: R165.2 (16.6, 105.275) → via (16.6, 104.5) → F.Cu y 98.45 → TP84 / C87 → via (40.42, 93.5) → B.Cu → U9.1. R7: x 1.5–10.5, y 37.5–41.5 | Correct M3_R8 l.243. Add BAT_ENABLE's crossing to R8_VALIDATION "Pyro review observations" with the latch analysis. In ORDERING §5's switch-cycle gate, add "board turns off with the link in" (cover it explicitly if the switch is the arming device) |
| R8P1-REQUIREMENTS-05 | Minor | Document accuracy (ORDERING is R8's per D81) | **ORDERING and records carry stale or inexact R8 facts.** (a) ORDERING §5 l.161, RF bench: "PD9 high-impedance … RADIO_NRST reads below 0.66 V". In R8 RADIO_NRST is on **PE9** and PD9 is RXEN (R7 text carried over). (b) ORDERING l.147: U4 "under U1's west edge". U4's courtyard is x 8.11–11.89, y 52.16–55.45 and U1's is x 14.36–31.64, y 36.35–53.65, so U4 is 2.5 mm west of U1, not under it. (c) ORDERING l.140: "J2's contact pads sit 0.84 mm from the left edge". That figure is the NPTH locating hole (x 1.334, Ø0.99); the contact pads' edge is at 1.32 mm. (d) M3_R8 l.38 / l.352, D76, STATUS: protection parts "within 4.6–10.6 mm of J1.1". R167's nearest pad is 3.86 mm away (centre 4.19 mm) | pcbnew pad and courtyard dump; `pin_table.tsv` rows 39 / 56 | (a) "PE9 high-impedance". (b) "west of U1". (c) "J2's locating hole 0.84 mm, contact pads 1.32 mm". (d) "3.9–10.6 mm" |
| R8P1-REQUIREMENTS-06 | Minor | REQUIREMENTS "R8 acceptance" (l.112): "two consecutive independent review passes" | **AGENTS §1 sets a weaker R8 ordering gate than REQUIREMENTS.** The manufacturing row (l.22) reads "Before ordering R8: an independent review pass with no open Critical or Major". STATUS and R8_VALIDATION say two consecutive passes | AGENTS l.22 against REQUIREMENTS l.112, STATUS l.42–43 | Write "two consecutive independent review passes with no open Critical or Major (REQUIREMENTS "R8 acceptance")" |
| R8P1-REQUIREMENTS-07 | Minor | STATUS consistency for the orderable fallback | **STATUS's R7 section contradicts itself.** The header (l.77–78) says pass 8 on the final board found 0 / 0. The review list ends "**No review pass on the fix-pass-7 board yet.**" (l.181), and open items say "then a review pass on the board that will be ordered" (l.234–235). R7_VALIDATION l.1270 records pass 8 on `c872a3d3…`. The text is inherited from R7's commit, but the R8 branch's STATUS now presents R7 as the board to order | STATUS l.77–78, 181, 234; R7_VALIDATION l.3, 791, 1270 | Replace l.181 with the pass-8 line and drop the stale open item |
| R8P1-REQUIREMENTS-08 | Minor | Repository front page versus STATUS (AGENTS §1) | **README presents M3-ASSY-R4 as current:** "two independently fused pyro channels", 46 × 193 mm, "aft ~70 mm sits inside the coupler", fourteen sheets, `r4_*.py`. R8 has one pyro channel, 46 × 118 mm and 15 sheets | README l.3–14 | Point README at STATUS / M3_R8 and state R8 candidate / R7 fallback, one pyro channel, 46 × 118 mm |
| R8P1-REQUIREMENTS-09 | Minor | REQUIREMENTS text currency for R8 | **Two R7-era statements in REQUIREMENTS are untrue for R8.** (a) P2 (l.67) still gives the no-sixth-support basis as "brings the first mode back to about R6's level". R8 is 209 Hz against R6's 241 Hz (−13 %), and R8_VALIDATION C10 asks the owner to rule; P2 does not point to C10. (b) M2 (l.75) names the poured nets as "GND, 3V3, 3V3A, BAT_IN, RAW_ACT, CAM_5V, ACT_FET_S". R8 has fills only on GND, 3V3, BAT_IN, RAW_ACT and ACT_FET_S, so 3V3A and CAM_5V fall under the net-level tests (`route_check` reads pours from the zones, so the gate is right and only the text is stale) | zone dump of `429b6db4…`; M3_R8 "Mechanical" | (a) Add "R8: f1 13 % below R6's; owner ruling open (R8_VALIDATION C10)". (b) "nets with a pour (on R8: GND, 3V3, BAT_IN, RAW_ACT, ACT_FET_S)" |
| R8P1-REQUIREMENTS-10 | Minor | F4 (l.54): "independently solve the final copper … including pad/via transitions and necks"; R7 P8-DOCS-02(f) | **Per-via currents of the 7.7 A via fields are still not reported.** MARGIN_PRESCRIPTION's R8 note (l.196) says the via fields "are not assessed for current". BAT_IN carries about 40 % on In2 at mid-path through 15 vias, 3 of them in the column at x 21.25 by Q120. Inference: about 1 A per via at worst, not alarming (0.3 mm / 20 µm barrel ≈ a 0.6 mm 1 oz track), but unstated | via list: BAT_IN 15 (21.25, 100.9 / 102.3 / 103.7; 17.7–26.2 × 105.6 / 107.0); RAW_ACT 66; M3_R8 layer shares | When the 0.05 mm solve is next run, print per-via barrel currents (R7 pass 8's `dc_via.py` method) and record the highest in M3_R8 "DC solve"; otherwise record it as a known gap |

### Severity notes

- **01 is Major, not Minor.**
  - R7 pass 8 rated two missing adjacencies Minor (P8-DOCS-01), on the grounds that adjacency is a review item, not
    one of M2's named routing defects.
  - Here the omission is categorical, and it includes M2's named "no needless detours" category for nets without a
    pour. R7 listed 38 such runs (C24 / C25), and the R7 pass-6 precedent for an unlisted category (P6-DOCS-01) was
    Major.
  - The copper is DRC-legal. The defect is that owner acceptance of this list would not make M2 true.
- **04 is Minor.** The latch needs an improbable under-mask leak, and BAT_IN adjacency already gives the same exposure.
  The issue is the untrue record statement and the missing assessment.

## 6. Deviation list audit (R8_VALIDATION l.104–169)

| Part | Check | Result |
|---|---|---|
| Owner summary counts | 3 / 0 / 10 / 93 | Match the gate and `route.json` |
| A (3) | Against `route.json` `allowed` | A1 (A8, 2.717 mm, `nognd_audit` 0), A2 6.45 / 3.72 mm, A3 5.00 / 2.61 mm: match |
| B | `LEFTOVERS` | Empty, gate OK |
| C (10 rows) | Each row's figures | C1 3.4 mm; C5 RAW_ACT_SENSE_MCU 2.63 / 0.69 mm (3.80×) and TXEN 2.30 / 1.25; C7 per D61; C8 = the six `power_via_no_gnd`. All match. **Missing categories: finding 01** |
| E (93) | Counts and attributions per category | 42 / 15 / 9 / 8 / 7 / 6 / 4 / 2: match, net by net (pass-throughs, segment-inside-pad pads, width-change nets, u_turn nets) |
| Hard gates (l.35–49) | Against r8_plan §2 | Honest overall. "C1 / C3 = 0 except owner-accepted inherent items (TXEN, A8)" is shown with A2 / A3 as "D11's agreed fallback". D11's fallback was R7's rigid limiter copper with two entries. R8 regenerated the copper and still has two (shorter) entries, which is consistent in spirit and awaits the owner like every entry |
| Scorecard misses | Measured causes (r8_plan §4 stop rule) | S8 / S9, P6, P7, P9 / P10, R6b and S15 each carry a cause. C2 (93 against ≤ 80) has only the E table, with no statement why the 42 off-centre pad ends cannot go without a priority-1 cost. Observation only |

## 7. Document consistency checked (no finding)

- **Board SHA `429b6db4…` and netlist `0cc1ed69…`:** consistent in STATUS, M3_R8, R8_VALIDATION, REQUIREMENTS F4 /
  M2 / M3, ORDERING, AGENTS, the binding note and the manifest.
  - The binding note's pin-table SHA `bd4687a8…` equals the file.
- **Counts:** 193 moved / 58 changed side (31 F→B + 27 B→F, measured); 89 / 130 / 24 TP / 5 DNP; 81 hidden; 92 BOM
  lines byte-identical to R7; 269 tests / 17 suites (17 `tools/test_*.py` files).
- **ORDERING figures confirmed:**
  - sled pours on B.Cu: RAW_ACT x 0.5–16.5 / y 81.8–108 and x 19.85–25.1 / y 70.9–86.9; ACT_FET_S x 9.6–14.78;
    BAT_IN x 15.02–41.3;
  - In2 3V3 at hole (4, 64) and BAT_IN at (42, 114.4);
  - NRST probe C24.1 (25.33, 51.1) and C15.1 (29.2, 49.82), 4.08 mm apart;
  - TP122 (20.45, 92.4); tab windows; order mark; DNP list.
- **MARGIN_PRESCRIPTION R8 notes (P1-9, R14 (R7))** agree with M3_R8.
- **REQUIREMENTS F4 / F10 / M2 / M3 R8 figures** agree with the gate and the records.

## 8. Observations (not findings)

- **D12's thresholds are written into F4 as R8's requirement**, taken "on the owner's behalf". The R8 values (17.5 /
  14.5 / 21.5 °C) are stricter than R7's owner-accepted values, so nothing waits on this. The owner may still want to
  confirm D12 with the R8 list.
- **The parent VEHICLE.md stack row still names R7.** D84 proposes the R8 row and it has not been applied. That is
  correct while R7 is the revision to order.
- **RAW_ACT pours (F.Cu, In2, B.Cu) reach 0.5 mm from the left edge at the forward-left tab (y 100–105).** The tab
  windows check parts and pads, not pours. This is for the DFM reviewer: nibble and file only, as ORDERING says.
- **Via spacing around U31:** the strip is rigid, and the F10 fence and gap figures match `check_r8`.

## Appendix A: scan methods (scripts in the session scratchpad, deleted after the pass; logic given here to reproduce)

- **Chain detours (01a).** For each net with no zone, I joined same-layer track ends (rounded to 1 µm) into runs.
  - A run ends at a node: a degree other than 2, a same-net via (inside its ring), or a same-net pad on that layer
    (`HitTest`).
  - I report a run of ≥ 2 segments when its length is > 1.25 × the octile distance of its ends
    (max(|dx|,|dy|) + (√2−1)·min) and > 0.5 mm longer.
  - On R7 `c872a3d3…` this gives 38 runs (= C24 21 + C25 17). On R8 it gives 27.
- **Adjacency (01b).** Every pair of different-net tracks, or track and via, on the same copper layer: segment-to-segment
  distance minus half-widths (via: ring radius) < 0.2 mm. On R8: 53 segment pairs, 32 net pairs.
- **Others.**
  - Via-copper steps: tracks with both ends inside a same-net via ring, off centre.
  - Poured-net hops: via-to-via tracks < 4 mm on poured nets.
  - Legend distances: text bounding box to pad centre.
  - BAT_ENABLE gaps: `SHAPE.GetClearance` between net items per layer.

## Appendix B: R8 measurements behind finding 01

### Chain detours on nets without a pour (27)

| # | Net (class) | Layer | Run ends | Run / octile mm | Excess mm | Segs |
|---|---|---|---|---|---|---|
| 1 | RAW_PROTECTED (critical) | F.Cu | (18.2, 103.79) – (45.2, 83.7) | 47.09 / 35.32 | 11.77 | 4 |
| 2 | BAT_ENABLE (non-critical) | F.Cu | (16.6, 104.5) – (40.42, 93.5) | 39.31 / 28.38 | 10.94 | 5 |
| 3 | RADIO_TXEN (critical) | B.Cu | (28.59, 7.8) – (31.13, 20.15) | 22.72 / 13.4 | 9.32 | 5 |
| 4 | PYRO1_CONT (critical) | B.Cu | (28.4, 88.61) – (23.17, 54.6) | 45.43 / 36.18 | 9.26 | 8 |
| 5 | USB_LIMITED (critical) | B.Cu | (19.4, 37.25) – (29.95, 54.0) | 27.3 / 21.12 | 6.18 | 2 |
| 6 | CAM_PWR_EN (non-critical) | B.Cu | (31.85, 43.0) – (30.775, 27.5) | 22.12 / 15.95 | 6.18 | 4 |
| 7 | GNSS_TXD_MCU (critical) | F.Cu | (22.5, 37.45) – (7.11, 22.75) | 26.87 / 21.48 | 5.39 | 7 |
| 8 | GNSS_TP_MCU (critical) | F.Cu | (23.5, 37.45) – (9.0, 22.88) | 25.97 / 20.58 | 5.39 | 7 |
| 9 | GNSS_RXD (critical) | F.Cu | (18.8, 29.17) – (8.21, 19.7) | 19.36 / 14.51 | 4.84 | 5 |
| 10 | PULLPIN (non-critical) | F.Cu | (20.5, 52.55) – (14.23, 61.0) | 14.43 / 11.05 | 3.38 | 3 |
| 11 | SPI1_SCK (critical) | F.Cu | (15.45, 45.5) – (10.0, 56.35) | 16.39 / 13.11 | 3.28 | 4 |
| 12 | VLOGIC (critical) | B.Cu | (26.95, 60.5) – (34.75, 65.65) | 12.95 / 9.93 | 3.02 | 3 |
| 13 | 3V3A (critical) | B.Cu | (11.21, 53.05) – (9.5, 52.84) | 4.6 / 1.8 | 2.8 | 3 |
| 14 | USB_DM (critical) | F.Cu | (6.88, 32.85) – (6.88, 33.85) | 3.36 / 1.0 | 2.36 | 3 |
| 15 | USB_DM (critical) | F.Cu | (12.6, 32.85) – (19.5, 37.45) | 11.03 / 8.81 | 2.23 | 5 |
| 16 | VBUS (critical) | B.Cu | (7.95, 29.2) – (11.225, 26.0) | 6.47 / 4.6 | 1.87 | 2 |
| 17 | QSPI_CLK (critical) | F.Cu | (30.55, 46.0) – (27.75, 42.57) | 6.23 / 4.59 | 1.64 | 3 |
| 18 | SERVO4_MCU (non-critical) | B.Cu | (32.6, 71.89) – (35.35, 74.55) | 5.12 / 3.85 | 1.27 | 3 |
| 19 | SERVO1_MCU (non-critical) | B.Cu | (32.6, 79.51) – (35.35, 76.85) | 5.12 / 3.85 | 1.27 | 3 |
| 20 | PYRO1_CONT (critical) | F.Cu | (26.83, 87.9) – (24.6, 87.2) | 3.61 / 2.52 | 1.09 | 4 |
| 21 | CAM_5V (critical) | B.Cu | (38.5, 47.4) – (40.8, 49.6) | 4.27 / 3.21 | 1.05 | 3 |
| 22 | CC2 (non-critical) | F.Cu | (6.88, 35.35) – (8.57, 37.2) | 3.54 / 2.55 | 0.99 | 2 |
| 23 | ACT_GATE (non-critical) | B.Cu | (10.9, 104.9) – (12.5, 107.16) | 3.86 / 2.92 | 0.94 | 2 |
| 24 | RADIO_RXEN (critical) | F.Cu | (25.8, 7.58) – (27.32, 9.05) | 2.74 / 2.13 | 0.62 | 3 |
| 25 | 3V3_GNSS (critical) | F.Cu | (13.71, 19.7) – (12.61, 20.75) | 2.15 / 1.53 | 0.62 | 2 |
| 26 | USB_DP (critical) | F.Cu | (6.88, 33.35) – (8.4, 34.35) | 2.52 / 1.93 | 0.59 | 2 |
| 27 | CAM_5V (critical) | B.Cu | (40.8, 49.6) – (39.5, 50.55) | 2.25 / 1.69 | 0.56 | 2 |

Some runs are L-shaped trunks or visit pass-through pads (#1 RAW_PROTECTED's east-edge trunk, D46; #2 BAT_ENABLE
through TP84.1 / C87.1). R7 listed such runs too, each with its reason. They still need a row and a measured reason,
or removal. #3 is covered by C5 / D10.

### Edge gaps under 0.2 mm between different nets (32)

| # | Gap mm | Layer | Nets | Items |
|---|---|---|---|---|
| 1 | 0.150 | B.Cu | CAM_FAULT_N / CAM_PWR_EN | trk (32.35, 43.5)–(32.35, 36.975); via (31.85, 43.0) |
| 2 | 0.150 | B.Cu | CAM_PWR_EN / USB_LIMITED | trk (28.0, 36.8)–(28.0, 27.5); trk (19.4, 37.25)–(29.95, 37.25) |
| 3 | 0.150 | B.Cu | GND / CAM_5V | via (41.4, 47.8); trk (40.4, 47.4)–(40.8, 47.8) |
| 4 | 0.150 | B.Cu | RAW_PROTECTED / VLOGIC | via (35.25, 60.5); trk (35.95, 59.275)–(35.95, 60.7) |
| 5 | 0.150 | B.Cu | SPI1_SCK / IMU_CS | trk (10.0, 56.35)–(10.0, 54.76); via (10.5, 55.65) |
| 6 | 0.150 | B.Cu | SPI1_SCK / SPI1_MOSI | trk (10.0, 56.35)–(10.0, 54.76); via (9.5, 55.65) |
| 7 | 0.150 | F.Cu | BUZZ_DRV / PULLPIN | via (16.4, 60.5); trk (20.0, 61.0)–(14.23, 61.0) |
| 8 | 0.150 | F.Cu | CAM_FAULT_N / CAM_PWR_EN | trk (30.55, 43.5)–(32.35, 43.5); via (31.85, 43.0) |
| 9 | 0.150 | F.Cu | CAM_MCU_RX / CAM_MCU_TX | via (31.85, 45.5); trk (30.55, 45.0)–(32.3, 45.0) |
| 10 | 0.150 | F.Cu | CAM_UART_OE / CAM_IO_3V3 | trk (32.5, 48.5)–(34.95, 48.5); via (35.45, 48.5) |
| 11 | 0.150 | F.Cu | GND / CAM_MCU_TX | via (33.9, 45.2); trk (33.05, 45.75)–(34.45, 45.75) |
| 12 | 0.150 | F.Cu | GND / RADIO_MISO_MCU | via (22.1, 23.3); trk (21.6, 30.086)–(21.6, 22.814) |
| 13 | 0.150 | F.Cu | GND / RADIO_MOSI | via (22.1, 23.3); trk (22.6, 29.07)–(22.6, 14.4) |
| 14 | 0.150 | F.Cu | GND / RAW_PROTECTED | via (41.45, 32.6); trk (42.15, 49.8)–(42.15, 25.6) |
| 15 | 0.150 | F.Cu | RADIO_NRST / CAM_MCU_RX | trk (33.4, 44.5)–(33.4, 31.0); via (33.9, 44.0) |
| 16 | 0.150 | F.Cu | RAW_ACT_SENSE_MCU / CAM_5V_SENSE | via (31.75, 47.0); trk (30.55, 46.5)–(33.3, 46.5) |
| 17 | 0.150 | F.Cu | SERVO1_MCU / VLOGIC | trk (27.5, 52.55)–(27.5, 79.01); via (26.95, 60.5) |
| 18 | 0.150 | F.Cu | USB_FAULT_N / LED_YEL | via (14.0, 44.5); trk (15.45, 45.0)–(13.3, 45.0) |
| 19 | 0.154 | F.Cu | I2C1_SCL / I2C1_SDA | trk (14.45, 48.5)–(12.0, 50.95); trk (12.5, 50.95)–(12.5, 60.32) |
| 20 | 0.173 | F.Cu | GND / ARM1_SENSE | trk (17.551, 90.727)–(18.927, 90.727); via (18.18, 91.3) (rigid R7 copper) |
| 21 | 0.175 | B.Cu | GND / CAM_IO_3V3 | via (40.375, 51.875); trk (39.8, 51.2)–(39.8, 55.0) |
| 22 | 0.175 | F.Cu | GND / GNSS_RESET_N | via (19.125, 25.875); trk (19.4, 26.4)–(15.41, 26.4) |
| 23 | 0.175 | F.Cu | GND / GNSS_RXD | via (7.685, 23.3); trk (8.21, 27.0)–(8.21, 19.7) |
| 24 | 0.176 | F.Cu | GND / GNSS_TXD_MCU | via (7.636, 25.327); trk (7.11, 27.6)–(7.11, 22.75) |
| 25 | 0.180 | B.Cu | GND / GNSS_ANT_DC | via (9.025, 8.325); trk (11.45, 5.15)–(5.85, 10.75) |
| 26 | 0.180 | F.Cu | GND / CC2 | via (9.1, 36.0); trk (8.57, 35.35)–(8.57, 37.2) |
| 27 | 0.180 | F.Cu | GND / LOGIC_SOURCE_ST | via (34.625, 52.875); trk (34.0, 51.5)–(38.6, 56.1) |
| 28 | 0.180 | F.Cu | RADIO_RXEN / GND | trk (21.0, 7.58)–(25.8, 7.58); via (22.0, 7.0) |
| 29 | 0.180 | F.Cu | SWDIO / USB_DP | trk (14.0, 36.4)–(11.5, 38.9); trk (12.55, 36.02)–(19.0, 36.02) |
| 30 | 0.180 | F.Cu | USB_DM / USB_DP | trk (13.0, 35.24)–(13.4, 35.64); trk (12.55, 36.02)–(19.0, 36.02) |
| 31 | 0.190 | F.Cu | VBUS_SENSE / USB_DM | via (16.6, 35.1); trk (13.4, 35.64)–(19.5, 35.64) |
| 32 | 0.198 | B.Cu | GND / BAT_ILIM | via (42.9, 87.6); trk (43.0, 86.925)–(43.8, 87.725) |

All are DRC-legal at the board's 0.15 mm default (JLC multilayer minimum 0.09 mm). On R7 the same scan gives 195 net
pairs, most of them inherited R6 copper that C15 did not list one by one. On R8 all but #20 (and the rigid strip GND via
side of #25) is new copper.
