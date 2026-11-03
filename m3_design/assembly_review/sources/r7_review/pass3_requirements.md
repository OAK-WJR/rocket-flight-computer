# R7 review pass 3: requirements conformance and documents

Reviewer: independent, pass 3, dimension "requirements conformance and documents".

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `7660620cfa834e4d381d2a2638780e9a341341c9b93c6e6f526791204dc77c9c`. That is the final pass-2-fix board named in
  R7_VALIDATION, STATUS and M3_R7. It was unchanged before and after this review.
- **Other inputs:** schematic `47057f7d97c7d748…`, `m3.kicad_dru` `1674d58be79ae428…` (the `DRU_SHA` that
  `check_actuators.py` pins).
- **Comparison boards:** R6 from `git show 3b215ba:m3_design/assembly_review/m3.kicad_pcb` (SHA-256 `184a87e8…6680`)
  and the pass-2 reports on `03fe7572…`.
- **Method:** read-only. Every measurement was taken on a scratch copy with KiCad 10.0.6 pcbnew, and the scripts sat
  in the session scratchpad. Bytecode writing was off. The only repository file changed is this report.

## 1. Summary

**Gate and tests reproduce clean on the final board.** `tools/check.sh` exits 0:
- DRC 0, unconnected 0, parity 0, ERC 0;
- audit OK, silkscreen 0 outside the outline;
- R7 contract OK, routing hygiene "0 failing, 20 allowlisted, 0 stale";
- actuator contract OK, fit OK.

All 157 unit tests pass in 9 suites (2 + 23 + 22 + 10 + 15 + 17 + 28 + 19 + 21). `tools/fab_manifest.py` is OK
(5 outputs). `check_procurement` passes `--cost-only` and fails the full gate on U4 stock, as documented.
`tools/dc_solve.py` reproduces RAW_ACT Q121 → J122 at 3.96 mΩ and BAT_IN J1 → Q120 at 3.91 mΩ (F4).

**Every pass-2 finding in this dimension is closed or properly dispositioned** (section 2). The J2 coating, the
vibration estimate and the via in R100's pad (the three pass-2 Majors) are closed in CAD and in the documents. P3
and ORDERING §5 now agree.

**New in pass 3:** 1 Major and 6 Minor findings.

- **Major P3-REQUIREMENTS-01: M2's clean-routing criterion is not met on the final board, and the gate passes
  anyway.** The owner's M2 bans "needless detours, extra vias or layer hops", staircases, tiny jogs and untidy pad
  entries over the whole board, inherited copper included. M2 then says this is "Enforced by
  `tools/route_check.py`". It is not:
  - `route_check` has no detour or via-count measure.
  - Layer hops and pad entries are information only.
  - Hygiene is gated on critical nets only.
  - 20 violations of AGENTS §3 / M2 are allowlisted in the tool, with no exception recorded in REQUIREMENTS and no
    owner acceptance.

  Measured examples, all inherited from R6 and not rerouted:
  - SWCLK: 117.2 mm with 14 vias on all four layers, for a 33.0 mm connection (3.55×). It runs 19.5 mm on In1, the
    GND plane, and loops through the pyro block to y 99.25.
  - CAM_PWR_EN: 81.9 mm with 8 vias (2.52×).
  - SWDIO: 70.8 mm with 11 vias.
  - CAM_MCU_TX: 2.67×.

  STATUS nevertheless lists "clean routing per M2" as "Shown in CAD".
- **Minor (documents):**
  - The R7 records still list the parent VEHICLE.md stack row and the CLAUDE.md E22 wording as open. Both were
    committed in the parent repository on 2026-10-16 (`43af048`).
  - REQUIREMENTS M3 and ORDERING §1/§4 still quote the 2026-10-16 cost and stock snapshot.
  - ORDERING was not updated for C304 or for TP89 moving to the bottom.
- **Minor (records and tools):**
  - A via hole opens into J2.1's mask opening. M2's wording does not exempt J2, and ORDERING's DFM list omits it.
  - `check_r7`'s RF-part safety-net check skips the limiter transistors Q30–Q32. No net actually violates it.
  - AGENTS §3, the P2 "owner decision" label and the binding note on interrupt vectors have small wording gaps.

**R7 acceptance (REQUIREMENTS, last section):**
- Met: the gate, M3 (US$105.96 per board, 52 extended codes, snapshot 2026-10-17 21:01Z) and the fab binding.
- Open: "no open Critical or Major" (P3-REQUIREMENTS-01), M1 stock (U4 consignment) and JLC's written confirmation
  of the forward rail.

## 2. Closure of the pass-2 findings in this dimension

| Pass-2 ID | Pass-2 severity (skeptic majority) | R7_VALIDATION disposition | Pass-3 check | Verdict |
|---|---|---|---|---|
| REQUIREMENTS-01 (J2 coating against P3) | Major → Minor | Documented (owner-delegated): J2 bare for programming, then polyimide tape and acrylic after the final SWD session; NRST gate | P3 (REQUIREMENTS l.68), ORDERING §5 (coating, J2 bullet, NRST gate, step order, static gate via C24) and MARGIN P1-13 agree. NRST pads on the board: J2.3, U1.14 and C24.1. C24.1 (NRST, bottom, (29.4, 47.92)) and C15.1 (3V3, bottom, (27.38, 45.9)) are the probe points ORDERING names, and their nets are right. The 0.97 × 3V3 ratio gives ≥ 1.07–1.93 MΩ with a 30–50 kΩ pull-up and a 10 MΩ meter (checked arithmetic). C24's bare NRST–GND pad gap is not coated, but the gate measures it (ORDERING says so) | **Closed** (bench gate open, as recorded) |
| REQUIREMENTS-02 (P2 span/vibration not re-derived) | Major | Fixed (record): M3_R7 §"Mechanical", no sixth support, sled carries the plugs | M3_R7 l.430–456 records method, inputs, f1 221–313 Hz (pinned, plugs on the sled) against R6 241–341, and the tap/modal bench step (ORDERING §5). It was computed on the pass-2 board. Outline, supports and masses are unchanged on the final board, so the Inference that it carries over holds | **Closed** |
| REQUIREMENTS-03 (via in R100.1) | Major | Fixed: via to (42.175, 55.82); `check_r7.vias_in_smd_pads` | My own whole-board scan (via hole edge to every pad mask opening) finds no via within 0.1 mm of a soldered pad's opening. CAM_RX_WIRE via at (42.175, 55.82), Ø0.3/0.6. The only hits are TP122 (bare, exempt) and J2.1 (see P3-REQUIREMENTS-05) | **Closed** |
| REQUIREMENTS-04 (F4 solve) | Minor | Fixed (M3_R7 §"DC solve") | F4 now points at M3_R7 §"DC solve" bound to `7660620c…`. My rerun: RAW_ACT 3.96 mΩ (30.5 mV, 0.235 W) and BAT_IN 3.91 mΩ (30.1 mV, 0.232 W) | **Closed** |
| REQUIREMENTS-05 (F10 strip wording) | Minor | Documented; the `check_r7` comment is open | F10 l.60 "What the strip may hold" matches `check_r7` STRIP_F/STRIP_B/STRIP_VIA and the `U30_KEEPOUT`/`U31_KEEPOUT` areas (U31's covers B.Cu/In2 over the whole body). The comment still points at the old exception list (recorded open) | **Closed** (tool note open, as recorded) |
| REQUIREMENTS-06 (VEHICLE stack, board position) | Minor | Open (parent repository) | Board position rewritten in REQUIREMENTS. **The parent row is no longer open:** parent commit `43af048` (2026-10-16 10:41 −0700) put the R7 stack in VEHICLE.md l.39 | **Closed in fact; record stale** (P3-REQUIREMENTS-02) |
| REQUIREMENTS-07 (LS120 reflow) | Minor | Fixed in documents; catalog open | M1 l.74 and ORDERING §4 cite datasheet §3 item 9. `procurement_catalog.json` (C94598) has no reflow field (recorded open) | **Closed** |
| REQUIREMENTS-08 (LS120 silk 0.12 mm) | Minor | Fixed | Board scan: no F/B.SilkS stroke under 0.15 mm; no visible text under 1.0 mm high or 0.15 mm thick | **Closed** |
| REQUIREMENTS-09 (RADIO legend on the bottom; lead labels) | Minor | Fixed | `GNSS` F.SilkS (8.05, 8.1); `RADIO` F.SilkS (35.74, 6.2); ORDERING §7: "Label both leads GNSS and RADIO" | **Closed** |
| REQUIREMENTS-10 (M3 wording; U4 owner cost) | Minor | Fixed | Wording is correct for the 2026-10-16 snapshot, but stale against the final run (P3-REQUIREMENTS-03) | **Closed; superseded figures** |
| REQUIREMENTS-11 (credit `check_r7`) | Minor | Fixed | F10, FMEA I-11/V-19, M3_R7 and STATUS credit `check_r7` (pad level) plus DRC and parity. The check skips Q30–Q32 (P3-REQUIREMENTS-06) | **Closed** |
| REQUIREMENTS-12 (SMA/module retention) | Minor | Documented (MARGIN R14 (R7)) | Row present. 1.8 g × 100 g × 5 = 8.8 N, matching its "≈ 9 N" | **Closed** |
| REQUIREMENTS-13 (a–d consistency) | Minor | (a), (b), (d) fixed; (c) open for the coordinator | (a) ORDERING §7 battery row, (b) FMEA V-19 body and (d) M3_R7 DIO1 3.06 mm are all present. **(c) is done:** parent CLAUDE.md now says "the E22-900M22S is a layout alternate that needs a respin" (`43af048`) | **Closed in fact; record stale** (P3-REQUIREMENTS-02) |

Also checked, from other dimensions where the requirement text changed:
- MECHANICAL-03: VEHICLE row done in the parent; the Onshape shroud measurement is still open.
- RF-03: F10's gaps reproduce on the final board with pass2_rf's method: GNSS west 4.27 mm ((11.6, 4.15) →
  (12.61, 8.30)), radio west 3.68 mm. Removing the two lattice vias left both unchanged. GNSS east grew
  2.18 → 2.74 mm, still below F10's quoted worst case.
- RG-05/RQ-01/RQ-06 and the 20 allowlist entries ("for pass 3 or the owner to accept"): judged under M2 in
  P3-REQUIREMENTS-01.

## 3. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| P3-REQUIREMENTS-01 | Major | REQUIREMENTS M2 (clean routing over the whole board, inherited copper included); REQUIREMENTS "R7 acceptance"; AGENTS §3; STATUS "Shown in CAD" | **M2 is not met on the final board, and the gate cannot show it.** M2 (l.75) requires: AGENTS §3, plus no needless detours, extra vias or layer hops, tiny jogs, untidy pad entries or neck-downs, "over the whole board, copper inherited from earlier revisions included". It then says "Enforced by `tools/route_check.py` in `tools/check.sh`". STATUS l.84 lists "clean routing per M2 (`route_check`, allowlist in M3_R7)" under **Shown in CAD**. R7_VALIDATION l.271–272 hands the residuals to "pass 3 or the owner to accept". No owner acceptance or requirement-level exception exists, and inherited routes clearly break M2's own list. | **1. Detours, extra vias and layer hops, never rerouted** (pcbnew, two-pad nets, copper length against the octile distance between the pads; R6 in brackets):<ul><li>**SWCLK** J2.4 (42.365, 76.65) → U1.76 (15.85, 61.05): **117.2 mm against 33.0 mm (3.55×), 14 vias, all four layers** (R6 118.0 mm, 14 vias). 19.47 mm of it is on **In1**, the GND reference plane: x 21.5–22.05, y 56.35–61.7 under U1, and y 65.3, x 15.7–19.5. It goes south into the pyro block (B.Cu (33.05–41.05, 99.15), In2 to (20.15, 99.25)) before turning back north to J2.</li><li>**CAM_PWR_EN** U1.84 → R74.1: **81.9 mm against 32.6 mm (2.52×), 8 vias**, down to y 99.75 and back (R6 82.0 / 8).</li><li>**SWDIO** J2.2 → U1.72: 70.8 mm against 36.3 mm (1.95×), **11 vias, four layers**, through (21.8, 86.4) in the pyro block (R6 70.8 / 11).</li><li>**CAM_MCU_TX** U1.46 → U12.5: 65.9 mm against 24.6 mm (2.67×), 5 vias (RQ-06, "residual").</li></ul>F3's handoff §7 and M3_R7 l.366 say only "not rerouted". Unlike the allowlist entries, no measured reason is given.<br>**2. §3 rule violations allowlisted in the tool, not in the requirement:** 5 staircases on critical nets (radio band ×4; PYRO1_CONT (34.72, 84.72), pyro class). PYRO1_CONT's allowlist reason is that it must thread "SWDIO (0.17 mm) and R77.1", so the inherited SWDIO detour in item 1 is what forces a staircase on a pyro net. Also 14 critical-net layer changes with no GND via within 1.5 mm (RADIO/GNSS ×10, PYRO1_GATE_N, PYRO1_CONT, ARM1_SENSE ×2). Each allowlist reason is a design trade-off ("needs the U1 escape re-spaced (not done)"; ARM1_SENSE: a GND via would raise BAT_IN 3.91 → 3.95 mΩ), not a physical impossibility.<br>**3. What `route_check` does not gate** (`tools/route_check.py` l.1–55, `GATE`):<ul><li>it has no detour or via-count category at all (no `net_length`/ratio code);</li><li>`short_layer_hop` (26), `pad_end_offcentre` (90 untidy pad entries), `u_turn` (25) and `extra_bends` (36) are information only;</li><li>hygiene categories gate only critical nets, so the 4 tiny jogs on CAM_EN, SERVO2_MCU, CAM_5V_SENSE and LOGIC_ILIM pass. My gate run: `route.json`, 244 instances, 0 failing, 20 allowed.</li></ul>So "Enforced by `route_check`" holds only for part of M2's list. | Decide it before pass 4, either way. (a) Reroute SWCLK, SWDIO and CAM_PWR_EN (J2 is 26–28 mm east of U1.72/76; no recorded obstacle forces the run south through the pyro block). That should also free PYRO1_CONT's staircase. Then reroute CAM_MCU_TX and the remaining allowlisted items where possible. (b) Or have the owner accept named deviations, and record them in REQUIREMENTS M2 as an exception list with measured reasons, the way M2 already points at M3_R4 §2 for thermal reliefs. In both cases:<ul><li>reword M2's last sentence to say what `route_check` enforces (the §3 rules on every net, hygiene on critical nets) and what is checked by review (detours, via count, layer hops, pad entries, non-critical hygiene);</li><li>add an information-only net-length/via-count report to `route_check`, so detours are visible in every gate run;</li><li>remove "clean routing per M2" from STATUS's "Shown in CAD" until M2 is met.</li></ul> |
| P3-REQUIREMENTS-02 | Minor | P1 (record the bay stack in the parent VEHICLE); document accuracy | **Parent-repository items are recorded as open but are done.** Parent commit `43af048` "Record the R7 flight-computer bay stack and the E22 alternate's respin" (2026-10-16 10:41 −0700) updated VEHICLE.md l.39 to M3-ASSY-R7, 46 × 118 mm, the five supports, the jacks, the 44–48 mm coax zone, the sled carrying the plugs and 52–68 mm slack. It also changed CLAUDE.md to "the E22-900M22S is a layout alternate that needs a respin". The R7 records, last updated 2026-10-17, still say otherwise. | <ul><li>M3_R7 l.280: "the parent `docs/VEHICLE.md` stack row still describes R5".</li><li>R7_VALIDATION l.205 (REQUIREMENTS-06 "Open (parent repository)"), l.212 (REQUIREMENTS-13 "Open (c)"), l.215 (MECHANICAL-03 "Open: parent VEHICLE.md row"), l.279.</li><li>STATUS l.107–108.</li><li>Parent `git log`: `43af048` touches CLAUDE.md and docs/VEHICLE.md (1 line each).</li></ul> | Mark REQUIREMENTS-06, REQUIREMENTS-13(c) and the VEHICLE half of MECHANICAL-03 closed (parent `43af048`). Delete the M3_R7 sentence. Keep only the Onshape shroud measurement and the plug choice open. |
| P3-REQUIREMENTS-03 | Minor | M3 (record of R7 as built); M1 stock; ORDERING accuracy | **Cost and stock statements are still on the superseded 2026-10-16 snapshot**, while M3_R7, STATUS and R7_VALIDATION use the final 2026-10-17 run. | **REQUIREMENTS M3** (l.76) still reads "R7 as built (…2026-10-16 05:14Z): **$110.93 per board** (parts $82.78…)", with the U4-consigned total "about $111.6–116.7".<br>**`fab/cost_check.json`** (checked 2026-10-17T21:01:10Z): parts $77.81, 92 codes, **52 extended, $105.96**, minimum-purchase $79.23, U4 line $8.39, U30 $17.38 with stock 161. **`stock_check.json`**: short U4 only, thin none.<br>**ORDERING §1** (l.28) "Result on 2026-10-16…$110.93…$84.20 once JLC's minimum purchases are counted". Its U30 note (l.32: "has thin stock: 18 in stock, about 10 available… Reserve it") is out of date: U30 now has 161 in stock. The §4 parts table says the same ("Thin stock: reserve"). M3_R7's parts table gives U30 "18 (ATP 9)", dated 2026-10-15; M3_R7 l.526 gives 161.<br>The bottom line is unaffected: M3 is met with margin either way. | Update M3's "R7 as built" line to the final run ($105.96 = $77.81 + 92 × $1.53 / 5; U4 consigned about $109.4–114.5). Update ORDERING §1's result paragraph and U30 note, or mark them as a dated historical snapshot and point at `cost_check.json`. Keep "reserve U30" as a precaution if wanted, but drop "thin". |
| P3-REQUIREMENTS-04 | Minor | ORDERING (build instructions), M2/F10 records; tool list | **Two pass-2 board changes did not reach ORDERING**, and one tool list lags. (a) **C304** (DNP, ELECTRICAL-01) is missing from ORDERING §1's expected `export_fab.py` output and from §4's DNP bullet. (b) **TP89 moved to the bottom**, but §4's test-pad split was not updated. (c) `check_r7.DNP` omits C304. C304 is still covered by `dnp_paste` and by `export_fab`'s rule that a DNP part left in the BOM stops the export. | (a) ORDERING l.25: "`not fitted (DNP placeholders, in no BOM or CPL): C303, C305, C313, C314`" and l.84 "DNP placeholders: C303, C305 … C313, C314". `tools/export_fab.py` l.177 prints every placeholder, and M3_R7 l.502 records "C303, C304, C305, C313, C314". An operator told the output "must report" the four-part list will see five.<br>(b) ORDERING l.80: "Top… plus 3 test pads; bottom… 21 test pads". Board: top TP30 and TP84 (2); bottom 22, including TP89 at (8.1, 33.6).<br>(c) `tools/check_r7.py` l.64 `DNP = ('C303', 'C305', 'C313', 'C314')`. | Add C304 to ORDERING §1 and §4. Change §4 to "2 test pads (TP30, TP84) … 22 test pads". Add C304 to `check_r7.DNP`. |
| P3-REQUIREMENTS-05 | Minor | M2 ("every via hole ≥ 0.1 mm from a pad opening (bare test pads may carry in-pad vias)"); ORDERING §3/§4 | **A 3V3 via hole opens into J2.1's mask opening.** M2's exemption names bare test pads. J2 is the TC2030 programming pattern, and only `check_r7` and M3_R7 exempt it. ORDERING's via rule ("Vias that cannot be ink-plugged (within 0.35 mm of a pad): tent them; never open the mask over a via") cannot be met at this via. Its "Expected DFM queries" list names only TP122's via. Inherited from R6, unchanged at (44.035, 59.92). | Via (44.035, 77.92), drill 0.30 mm, 3V3. J2.1 is a Ø0.787 mm `connect` pad at (43.635, 77.92), mask expansion 0. The hole edge is **0.14 mm inside** the opening (the via centre is outside). My scan (`meas2.py`) finds only this and TP122 (in-pad, exempt). `check_r7` l.99 `BARE_CONTACTS = ^(TP\d+|J2)$`; M3_R7 l.478–479 states it. P3 now has J2 taped and coated before flight, which covers the hole. | Name J2 in M2's exemption, or move the via about 0.15 mm east, since it is 3V3 only. Add the J2.1 via to ORDERING's expected DFM queries. |
| P3-REQUIREMENTS-06 | Minor | F10 ("no pin of an RF part sits on a pyro, arming, actuator, RAW_ACT, BAT_IN, BOOT0 or NRST net (`tools/check_r7.py`, pad level)"); FMEA I-11; STATUS; M3_R7 | **`check_r7`'s RF-part filter skips Q30, Q31 and Q32**, the antenna-bias limiter transistors. The pattern `[RCDLQ]3\d\d` needs three digits after the letter, so `Q30` never matches. The documents say every RF part is covered. | `tools/check_r7.py` l.370 `re.fullmatch(r'(U3[01]\|J3[01]\|[RCDLQ]3\d\d\|D3[01]\|L30\|FB3[01]\|TP30)', ref)`. Tested: Q30/Q31/Q32 False; R300, C304, D30, L30, FB30, TP30, U30 True. Netlist: Q30–Q32 sit only on GNSS_ANT_DC/GATE/PD/SRC, GNSS_LNA_EN, GNSS_VCC_RF and GND, so no violation exists today. | Use `Q3\d` (or `[RC]3\d\d\|Q3\d`) and add a test case. |
| P3-REQUIREMENTS-07 | Minor | AGENTS §3 against M2; P2 wording; F10 binding note | **Three small wording gaps between documents.** (a) AGENTS §3, the development rule every agent reads, does not mention M2's wider list or `route_check`. Its "add ground vias next to layer changes" covers all nets, while M2 and `route_check` scope it to critical nets within 1.5 mm. (b) P2 says "No sixth support (**owner decision**, R7 review pass 2)", while M3_R7 l.444 and the docs handoff call it "owner-delegated". (c) The F10/M3_R7 binding note records the shared EXTI9_5 vector (BUSY/USB_FAULT_N) but not EXTI15_10: DIO1 is EXTI10 (PD10, U1.57) and PULLPIN is EXTI14 (PC14, U1.8), and F10 itself says PULLPIN uses EXTI14. | AGENTS.md l.42; REQUIREMENTS l.67, l.60; M3_R7 l.143–145; netlist U1.57 RADIO_DIO1 PD10, U1.8 PULLPIN PC14. EXTI lines 10–15 share one NVIC vector on STM32H7 (RM0433 vector table; not re-read here, the same fact that underlies ELECTRICAL-03 for EXTI9_5). | (a) Point AGENTS §3 at REQUIREMENTS M2 and `tools/route_check.py`, with the same critical-net scope. (b) Use one attribution: "owner-delegated decision" or the owner's own record. (c) Add "DIO1 shares EXTI15_10 with PULLPIN: the handler checks both pending bits" to the binding note. |

## 4. Requirement walk (final board `7660620c…`)

Verdicts:
- **Pass:** shown on the board, schematic, gate or fab files.
- **Fail:** not met.
- **NV:** not verifiable in CAD (bench, flight or firmware).
- **Partial:** the CAD part passes and the rest is open.

### Sources and owner decisions

| Item | Verdict | Evidence |
|---|---|---|
| One primary pyro channel; isolated Blue Jay | Pass | `check_r7` REMOVED set (no CH2); no backup interface (AGENTS §1) |
| 4-servo limit | Pass | J122 3 × 4; `check_actuators` OK |
| On-board MAX-F10S and E22-900MM22S, JLC-assembled | Pass | BOM U30 C30005563 and U31 C5333985 (SMT); CPL top, not flipped |
| Uplink never arms or fires | Pass (CAD) | No RF-part pin on a safety net (`check_r7`; Q30–Q32 checked by hand, P3-REQUIREMENTS-06); ARM is the physical J124 link |
| Parent CLAUDE.md avionics paragraph (on disk, `43af048`) | Pass | STM32H743, 4 servos, single pyro, isolated Blue Jay, ≤ 120 mm (118), edge SMAs, E22 respin alternate: all agree with R7 |

### Functional

| ID | Verdict | Evidence / remark |
|---|---|---|
| F1–F3 | Pass (parts) | U4 LSM6DSV320X, U5 MS5611, unchanged from R6 |
| F4 | Partial | Outputs pass (`check_actuators`). The final-board solve is recorded (M3_R7 §"DC solve"), and I reproduced RAW_ACT 3.96 mΩ. Thermal-camera stall test: bench |
| F5 | Pass (part) | U3 W25Q128 |
| F6 (hardware) | Pass (CAD) | Servo pull-downs and pyro gate networks (`check_actuators`); R311/R310/R312 (`check_r7`); C24 100 nF on NRST unchanged |
| F7 | Pass (CAD) | One channel; R134, Q124; budget is calculation and bench |
| F8 | Pass (CAD) | DRC 0 under the nine pyro rules A–H plus A2 (`m3.kicad_dru` l.55–90; the R7 rules come first, so they cannot override a pyro rule). Legends ARM/IGN/BAT/1:BAT+, GNSS and RADIO on top. Bench gates NV |
| F9 | Pass (CAD part) | Unchanged R6 circuit; modules on regulated 3V3 |
| F10, strip and outline | Pass | Strip y 0–23.5; `check_r7` strip net lists OK (F.Cu 67, B.Cu 30 items, 202 vias); keep-outs U30 (F.Cu/In1) and U31 (all layers, and the whole body on B.Cu/In2) |
| F10, pin contract | Pass | `check_r7` RF_MCU_PINS and MODULE_PINS OK; netlist spot check of U1.45/55/57/61 |
| F10, RF distances | Pass | Nearest RF-part courtyard to a buck: FB30–U2 6.84 mm (M3_R7: ≥ 5.87 mm to C6). U30–U2 9.66 mm, U30/U31–L1 10.9 mm. Nearest fast-digital copper (QSPI/SPI1/USB/HSE/IMU_CS/SWD) to any RF part: 11.13 mm (U30 to U3.5 QSPI_IO0) |
| F10, GCPW and stitching | Pass (as accepted in F10) | W 0.30 by DRC rule; gaps GNSS west 4.27, radio west 3.68 (reproduced, §2) |
| F10, bench clauses (isolation, pyro immunity, limiter current) | NV | ORDERING §5 steps present |
| F10, binding constraints | Partial | EXTI9_5 and TIMEPULSE notes present; EXTI15_10 missing (P3-REQUIREMENTS-07c); no firmware binding (recorded) |

### Physical

| ID | Verdict | Evidence |
|---|---|---|
| P1 | Pass | Outline 46 × 118 (`check_r7`); fit OK; stack recorded in M3_R7 and the parent VEHICLE (P3-REQUIREMENTS-02) |
| P2, envelopes, supports, ties | Pass (CAD) | Fit margins: J9 mated 0.03, C84 0.11 mm. Nearest bottom envelope C76 4.150 mm (≥ 3.5); top TP30.1 5.008 mm; 5 supports at the stated holes; tie holes (21.5, 68.6) and (27.0, 82.6) |
| P2, span/vibration | Pass (record) | M3_R7 §"Mechanical"; bench tap check open |
| P3, retention / R14 (R7) | Pass (record) | MARGIN R14 (R7); staking and torque in ORDERING §5 |
| P3, no vias/fill under MEMS | Pass | `IMU_body_B` (34.35–37.65 × 76.91–79.69) and `BARO_body_B` (33.76–38.84 × 70.91–75.09) on B.Cu, no via, no fill; DRC 0 |
| P3, pyro block and J2 coated, NRST gate | Pass (procedure) | P3 and ORDERING §5 agree; bench open |

### Manufacturing and cost

| ID | Verdict | Evidence |
|---|---|---|
| M1 | Pass, except U4 stock (allowed) | Thickness 1.6; stackup as recorded (pass 2; job file regenerated); 219 CPL rows (96 top, 123 bottom); stock short U4 only; reflow texts consistent with ORDERING §4 |
| M2, JLC rules, courtyards, silk, via-in-pad | Pass (minor wording, P3-REQUIREMENTS-05) | DRC 0. No pad outside its courtyard (scan). No silk under 0.15 mm, no text under 1.0 mm. Via scan as in §2 |
| M2, clean routing | **Fail** | P3-REQUIREMENTS-01 |
| M3 | Pass | $105.96, 52 / 52 extended, snapshot 2026-10-17 21:01Z |

### R7 acceptance

| Condition | Status |
|---|---|
| `check.sh` zero; actuators, fit and `route_check` OK | Met (reproduced) |
| Independent review with no open Critical or Major | **Not met:** P3-REQUIREMENTS-01 (this dimension) |
| M3 on a ≤ 24 h snapshot | Met now (2026-10-17 21:01Z); rerun before ordering |
| M1 stock, U4 by consignment | Open |
| Fab outputs regenerated and bound | Met (`fab_manifest.py` OK) |

## 5. Document consistency (beyond the findings)

These agree with one another and with the board:
- REQUIREMENTS P2, P3, F10, M1 and the board-position assumption;
- ORDERING §5 and §7 (coating sequence, NRST gate, staking, tap check, hardware sizes, lead labels);
- MARGIN P1-13 and R14 (R7); FMEA I-11, V-19 and §6.3; AGENTS §1;
- STATUS's test counts (157 = 136 in 8 suites + 21);
- the hidden-designator list (89 on the board, identical to M3_R7 l.461–466);
- the legends; the BOM/CPL counts (92 lines = 92 codes, 219 rows).

Everything else is in P3-REQUIREMENTS-02 to -07.

Already recorded as open in R7_VALIDATION, not raised again here:
- `procurement_catalog.json` LS120 reflow;
- the `check_r7` strip comment;
- MARGIN's 85 °C list (E11);
- U4 consignment path (R7P1-18);
- the J123.1–CAM_5V 0.20 mm pad gap;
- the forward panel rail.

## 6. Measurements and reproductions

- **Gate:** `tools/check.sh` (2026-10-17, temporary copies), exit 0. Output as quoted in §1.
- **Fit:** "board: 46 x 118 mm; 120 mm maximum (P1)"; five-support geometry (4, 4), (4, 64), (4, 114.4), (42, 114.4),
  (42.3, 4).
- **Tests:** test_check_shell 2, test_fab_validation 23, test_fit_check 22, test_maze_clearances 10,
  test_procurement 15, test_r6_check 17, test_r7_check 28, test_route_check 19, quality_audit 21. All OK
  (KiCad Python, `PYTHONDONTWRITEBYTECODE=1`).
- **Fab and procurement:** `tools/fab_manifest.py`: "OK; 5 outputs". `check_procurement.verify(cost_only=True)` OK;
  the full check fails on "stock_check.json: procurement target is not met" (U4).
- **DC:** `tools/dc_solve.py` default (RAW_ACT Q121:5–9 → J122:2,5,8,11, grid 0.1): R = 3.96 mΩ, 30.5 mV, 0.235 W at
  7.7 A, 100 % F.Cu at mid-path; BAT_IN J1:1 → Q120:5–9: R = 3.91 mΩ, 30.1 mV, 0.232 W, 100 % In2 at mid-path.
- **Scratch scripts** (session scratchpad `p3req/`):
  - `meas1.py`: silk widths and text, hidden designators, legends, test-pad sides, courtyards, NRST/C24/C15 nets,
    positions;
  - `meas2.py`: via hole to every pad mask opening;
  - `meas3.py`: F10 distances;
  - `meas4.py`: rule areas and MEMS;
  - `meas5.py`/`meas6.py`: two-pad net length, octile ratio, vias, per-layer geometry (run on R7 and on R6);
  - `meas7.py`: pass2_rf §3.6 stitching gaps.
- **Two-pad nets at 1.8× or more, or with 4 or more vias (R7):** VCAP1 4.89× (6.7 mm over 1.4 mm with 2 vias:
  capacitor on the other face), VCAP2 4.22×, SWCLK 3.55× / 14 vias, CAM_MCU_TX 2.67× / 5, CAM_PWR_EN 2.52× / 8,
  RADIO_TXEN 2.30×, CAM_FLT_RAW 2.26×, SERVO2_OUT 2.19×, BAT_SW_RETURN 2.10×, SWDIO 1.95× / 11, SERVO4_OUT 1.83×,
  RADIO_DIO1 1.77× / 4, BAT_SW_SOURCE 1.48× / 7, CAM_MCU_RX 1.24× / 6.
- **Parent repository:** `git log`: `43af048 Record the R7 flight-computer bay stack and the E22 alternate's respin`
  (CLAUDE.md and docs/VEHICLE.md). VEHICLE.md l.39 is the R7 row; uncommitted edits by others elsewhere in that file
  were not touched.

## 7. Sources

- Repository documents as cited by line:
  - REQUIREMENTS, STATUS, ORDERING, M3_R7, R7_VALIDATION, MARGIN_PRESCRIPTION, FMEA_REDUNDANCY, AGENTS;
  - `fix2_F1/F2/F3/docs_handoff.md`;
  - pass-2 reports and verdict JSONs;
  - `tools/route_check.py`, `tools/check_r7.py`, `tools/export_fab.py`, `m3.kicad_dru`.
- JLC data as captured in `fab/cost_check.json` and `fab/stock_check.json` (source "jlcpcb.com
  selectSmtComponentList", 2026-10-17T21:01–21:02Z).
- STMicroelectronics RM0433 (STM32H7 reference manual), NVIC vector table (EXTI9_5 and EXTI15_10 shared vectors):
  not re-read in this pass.

## 8. Inferences (not checked against a primary source)

- "Needless" in P3-REQUIREMENTS-01 rests on two things: the detours have no recorded reason, and SWCLK, SWDIO and
  CAM_PWR_EN run south into the pyro block, away from J2. I did not probe a candidate reroute for clearance.
- The EXTI15_10 sharing (P3-REQUIREMENTS-07c) is standard STM32H7 vector assignment, not re-read in RM0433.
- The U4-consigned total in P3-REQUIREMENTS-03's fix ($109.4–114.5) applies REQUIREMENTS' own consignment range
  ($11.87–16.96) to the final run with JLC's U4 line ($8.39) removed.
