# R7 review pass 2: documentation fixes (handoff)

Documentation fix agent, pass 2. Files changed: `docs/REQUIREMENTS.md`, `docs/ORDERING.md`,
`docs/MARGIN_PRESCRIPTION.md`, `docs/FMEA_REDUNDANCY.md`. Not touched: the board, scripts, tools,
`docs/M3_R7.md`, `docs/R7_VALIDATION.md`, `STATUS.md`, `AGENTS.md` and the parent repository. Nothing committed.
Findings and verdicts: `pass2_*.md`, `pass2_main_verdicts.json`.

## 1. Changes per finding

| Finding | Decision | What changed |
|---|---|---|
| REQUIREMENTS-01 (J2 coating vs P3) | Owner-delegated: J2 stays a bare TC2030 pattern for programming. After the final SWD session before flight, its pads and locating holes are covered with polyimide tape and the pyro-block acrylic goes over the tape. Re-flash by USB DFU or by stripping J2 locally. Bench gate after coating: NRST-to-GND ≥ 1 MΩ | **REQUIREMENTS P3:** bold clause rewritten ("pyro block coated, J2 covered and coated after the final SWD session"), with the reason (NRST pad 0.48 mm from GND, held only by the 30–50 kΩ internal pull-up; Inference: about 13–21 kΩ holds reset, release not guaranteed below about 117 kΩ), the tape-then-acrylic procedure, the re-flash route and the gate. **ORDERING §5:** coating heading now covers J2; new J2 bullet (procedure, re-flash, re-coat); new **NRST gate** bullet; J2 added to the keep-off list until its last SWD session; step order gains "final SWD session → coat pyro block and J2 over tape → … NRST gate"; static gate can hold reset across C24 once J2 is coated; R134 probing note. **MARGIN_PRESCRIPTION P1-13 (§4.13) note:** "NRST on J2.4" replaced by the R6/R7 TC2030 decision (pad 3). **FMEA §6.3** bench line: "J2 flies bare and coated" replaced by the decision |
| MECHANICAL-01, REQUIREMENTS-12 (SMA retention) | Counter-hold, torque, stake, sled carries plugs | **REQUIREMENTS P3:** counter-hold the 6.5 mm square flange whenever a plug nut is turned; mating torque about 0.45 N·m, never above Kinghelm's 1.13 N·m; nuts witness-marked; structural-epoxy staking after the RF bench tests (flange back face to edge, along the GND legs on both faces, off the centre pad/RF line, threads and mating face); the sled carries both plugs and coax (tie or saddle at each crimp ferrule about 25–30 mm aft of the edge); U30/U31 need no staking; R14 now points at its R7 row. **ORDERING:** §4 parts table J30/J31 row; §5 counter-hold rule (in "First power-up", covering VNA, loads and antennas), J30/J31 added to the staking list with U30/U31 marked no staking/adhesive, step order "staking (J30/J31 included)"; §7 "Antennas and coax" and "Sled" rows rewritten (the old "end at the aft edge" option and the 2 cm tie are gone). **MARGIN_PRESCRIPTION §7:** new row "R14 (R7)": plug on the jack not shown (≈ 47–69 N per leg at 5 × 100 g; torque 78–111 N per leg if not counter-held); with the sled carrying the plug, jack only ≈ 1.8 g → ≫ 5× (Inference), U30/U31 ≫ 5× (maker masses) |
| MECHANICAL-02, REQUIREMENTS-02 (support span / vibration) | Owner-delegated: no sixth support; the sled carries the plugs | **REQUIREMENTS P2:** records the decision and why (plug mass off the aft edge brings f1 back to about R6's level, pass2_mechanical); the re-derivation is to be recorded in M3_R7 with the plugs carried by the sled; bench tap/modal check on the sled with both coax leads fitted. **ORDERING §5:** new "Tap or modal check on the sled" bullet (external accelerometer, compare with the M3_R7 estimate, a much lower f1 or plug-driven rocking goes back to the owner); added to the step order. The estimate itself is for the records agent (§3) |
| MECHANICAL-03, REQUIREMENTS-06, MECHANICAL-04 (bay stack, board position, coax zone) | pass2_mechanical wording | **REQUIREMENTS operating assumption "Board position":** the infeasible "aft edge about 70 mm below the coupler's forward end" (joint +50) replaced by: aft edge at joint ≥ +80…+83 mm (loops away from the shroud side) or ≥ +91…+95 mm (loops forward of the shroud), fixed after the Onshape shroud measurement; coax zone about 44–48 mm with axially staggered loops (≥ 1 cable OD) or right-angle plugs; choose the plug and coax and cite its drawing. **REQUIREMENTS P1:** cites the 44–48 mm zone. **ORDERING §7:** "Antennas and coax" (plug choice and drawing, loop zone) and "Sled" (board position, 52–68 mm slack). Parent VEHICLE.md text for the coordinator: §2 |
| MECHANICAL-05 (mounting hardware) | — | **ORDERING §7 "Mounting hardware":** M3 nylon screws and nuts, nylon washers ≤ 7.0 mm OD, nylon standoffs ≤ 5.5 mm across flats (≤ Ø6.4 mm) and ≥ 3.5 mm tall; TP89 3.86 mm from (4, 64) explains the washer limit; BUZZ_DRV added to the copper-near-hole list. **REQUIREMENTS P2** points at ORDERING §7 for sizes |
| RF-03 (stitching gaps) | Accept | **REQUIREMENTS F10:** the GCPW clause now records the largest continuous gaps, 4.27 mm (GNSS west) and 3.68 mm (radio west), accepted as under λ/20 in FR4 at 1.61 GHz (about 4.4 mm), with In1 continuous. The wrong "2.17–2.98 mm" figures are in M3_R7, R7_VALIDATION and stepB_handoff (records agent, §3) |
| RF-04, REQUIREMENTS-05 (what the strip may hold) | Amend F10 | **REQUIREMENTS F10:** "every copper layer GND outside the module pads and RF lines" replaced by a "What the strip may hold" clause: In1/In2 GND only; F.Cu/B.Cu GND outside the module pads, the RF lines and each module's own supply and interface traces; the bias limiter on B.Cu under U30; nothing but GND across U31's pad field on any layer (EBYTE §4.1, as REQUIREMENTS-05 proposed); under U30 the top two layers carry only GND and U30's own escapes; `check_r7.py` enforces the net lists. Also notes the radio's quasi-static control lines near U30 are not "fast digital lines" (pass2_rf §3.10) |
| ELECTRICAL-02 (antenna side) | — | **REQUIREMENTS F10:** the antenna must draw ≤ 20 mA and be rated to work from a supply as low as 2.7 V (limiter's hot limit about 25–38 mA at +85 °C; both board limits rest on inferred values). **ORDERING §7 "Antennas and coax":** same requirement. **ORDERING §5** GNSS short test: record the measured VCC_RF drop. I read the finding's "minimum supply ≥ 2.7 V" as "the antenna works from 2.7 V" (its minimum rated supply is 2.7 V or lower) |
| ELECTRICAL-03 (EXTI pin contract) | — | **REQUIREMENTS F10** binding note: BUSY (PD8, EXTI8) polled, or the EXTI9_5 handler (shared with USB_FAULT_N, PD6) tells the lines apart; TIMEPULSE (PD14) on TIM4_CH3 input capture, never EXTI14 (PULLPIN, PC14). M3_R7 pin contract: records agent |
| ELECTRICAL-04 (GNSS ESD) | Handling rule | **ORDERING §5 "First power-up":** GNSS antenna ESD rule (connect or disconnect only unpowered on an ESD-safe bench, never hot-plug in the field) with the reason (D30 clamps 20–48 V at 1–16 A TLP; RF_IN ±5.5 V DC, no ESD figure). Repeated in §7 "Antennas and coax"; the §5 GNSS short test now fits the short unpowered. The trade-off note in M3_R7 §"RF chains" is for the records agent |
| REGRESSION-07, REQUIREMENTS-04 (F4 solve) | — | **REQUIREMENTS F4:** "has not been re-solved" removed. F4 now says the R7 solve (RAW_ACT, BAT_IN, ACT_FET_S; `tools/dc_solve.py` on the final board, bound to its SHA-256) is recorded in **M3_R7 §DC solve**, and the R5/R6 solves are historical. No numbers in F4: the F3 fix agent reruns the solve, and the records agent writes the values and SHA into M3_R7 |
| DFM-03, DFM-04 (panel tabs) | Request plus confirmation step | **ORDERING §3:** delivery format now asks for a third rail on the forward edge with two 5 mm tabs at x 6–11 and x 35–40 (Gerber X 6…11 / 35…40, Y −118; ≥ 2.06 mm from J1, ≥ 7.45 mm from C76, off the forward M3-hole webs); both added to the tab table. The "Open: forward end" paragraph is replaced by a gate: before approving production, JLC confirms in writing either the forward rail or assembly with the forward 50 mm unsupported. Left tab (1.83 mm from J3, under JLC's 2 mm connector keep-out) accepted: ask JLC to leave out the one or two perforation holes nearest J3, nibble that tab last from the side away from J3, re-inspect J3's shell legs. The copper setback sentence now says board edges, not long edges. **§4 order remarks** carry both requests |
| DFM-05, DFM-06 (jack soldering) | — | **ORDERING §4 order remark:** inspect D30/D31 after soldering each jack. **ORDERING §5:** J30/J31 inspection now covers all four leg fillets top and bottom (visual or X-ray, with the reason), D30/D31 bridges or shift, and **an ohmmeter check of each jack's centre to shell before any power-up** (J31 open; J30 diode-like, not a short, Inference). "First power-up" requires that check first |
| DFM-08, REQUIREMENTS-07 (LS120 reflow) | Close R7P1-13 | **REQUIREMENTS M1** and **ORDERING §4** record the MLT-5020 rating (250 °C peak, ≤ 10 s above 245 °C, preheat 170–190 °C for 90 ± 30 s, ramps ≤ 4 °C/s; datasheet §3 item 9, LCSC URL); the "confirm before ordering" item is removed. **ORDERING §6** LS120 row updated. `procurement_catalog.json` (DFM-08 fix) is not mine: board/tools agents |
| DFM-09 (U30 reflow) | — | **REQUIREMENTS M1:** U30 245 °C peak, 40–60 s above 217 °C (u-blox IM §5.2), exactly Standard's upper bound, and U31 230–250 °C, TAL 30–90 s (EBYTE §7.1). **ORDERING §4:** service bullet carries both; new order remark: final (top) reflow peak ≤ 245 °C, 40–60 s above 217 °C, please confirm |
| REQUIREMENTS-10 (cost wording) | — | **REQUIREMENTS M3:** R7 line rewritten on the one `jlc_cost.py` snapshot (2026-10-16 05:14Z): $110.93 = parts $82.78 + 92 codes × $1.53 / 5, 52 extended; RF-strip lines listed as lines of that snapshot; R7 adds 14 codes (7 extended) and removes 4 (3 extended), net +10 codes, +$3.06 per board in feeder fees (I checked the code lists against R6's committed `cost_check.json`: 82 → 92 codes); R6's total is from an older snapshot, so the lines do not reconcile the difference; consigned U4 (7–10 at about $8.48) costs the owner $11.87–16.96 per board plus shipping, about $111.6–116.7 per board in all, within the cap. The "$5.77/board saved" figure is dropped (other snapshot) |
| REQUIREMENTS-11 (credit check_r7) | — | **REQUIREMENTS F10** (radio use) and **FMEA I-11/V-19 summary row:** RF isolation credited to `tools/check_r7.py` at pad level (no RF part pin on a PYRO/ARM/ACT_/RAW_ACT/BAT_IN/BOOT0/NRST net) plus DRC and schematic parity. STATUS's "(`check_actuators`)" credit is for the records agent |
| REQUIREMENTS-13 (consistency) | — | (a) **ORDERING §7 battery row:** "≥ 2 Ah if the radio transmits continuously on the pad" added. (b) **FMEA V-19 body:** "no telemetry on board; LoRa is unfitted pads only" removed; an R7 note says the on-board GNSS and LoRa radio can report position after landing once firmware has a LANDED state, but share the flight computer's pack, MCU and supply, so the independent tracker stays recommended. (c) Parent CLAUDE.md wording for the coordinator: §2. (d) M3_R7's 3.2–4.7 mm vs 3.03 mm: records agent |
| Owner clean-routing criterion | — | **REQUIREMENTS M2:** clean routing over the whole board, inherited copper included: AGENTS.md §3 plus no needless detours, extra vias or layer hops, micro-segments or tiny jogs, unmerged collinear segments, overlapping or duplicate copper, overlap-only joints, crossings without a node, untidy pad entries, width changes or neck-downs away from pads, or autorouter debris; enforced by `tools/route_check.py` in `tools/check.sh`; verified by "CAD, tools". **R7 acceptance** and **ORDERING §1** name the routing check. `tools/route_check.py` did not exist in this worktree when I wrote this, so the board/tools agents must land it under that name or the records agent must correct the name |

### Implementation details the records agent may need

- **NRST gate method.** An unpowered ohmmeter reading from NRST to GND runs through the internal pull-up, the
  MCU's protection diodes and the 3V3 rail's loads (pass2 verdict on REQUIREMENTS-01), so it cannot show 1 MΩ.
  ORDERING §5 therefore takes the reading powered (MCU running or blank, not in reset) with a 10 MΩ DMM: NRST at
  C24 pad 1 ≥ 0.97 × 3V3 measured at C15 pad 1. Both are on the bottom side next to each other; I checked their
  nets and positions in pcbnew. With RPU 30–50 kΩ and the meter's 10 MΩ, 0.97 means ≥ about 1.07–1.9 MΩ of leak.
  A healthy board reads about 0.995 (Inference, typical NRST characteristics). Once J2 is coated, reset is held
  for the static and leakage pyro gates by shorting across C24's two pads.
- **J2 timing.** J2 is coated together with the pyro block if the flight firmware is final by then. If not, it is
  coated after the last SWD session, and the NRST gate and the static gate are repeated then.
- **No new numbers were invented.** The figures come from pass2_mechanical (§3.4–3.6, the appendix masses),
  pass2_electrical §4.3, pass2_rf §3.6, pass2_dfm and the verdict files. They are labelled Inference wherever the
  source labels them so.

## 2. For the coordinator (parent repository, not edited)

**Parent `docs/VEHICLE.md`, "Main-section stack, bulkplate up" row.** That file has uncommitted edits by someone
else, so merge with them. Proposed text:

> 2S battery bay ~80 mm, battery leads and RF coax loop zone ~44–48 (jack 9.5 + straight SMA plug ~16–20 + two
> RG316 loops at 13 mm bend radius, axially staggered by ≥ 1 cable OD, or right-angle plugs; off the camera-shroud
> side between joint + 4 and + 47), flight computer board 118 (M3-ASSY-R7, 46 × 118 mm, parts on both sides; two
> edge-launch SMA jacks on its aft edge reach 9.5 mm beyond it; J1's battery entry faces forward at the board's
> forward edge, so the battery leads run the board's length; it fits the Ø50.8 mm coupler bore along its whole
> length; the sled puts the board's top face on the bore axis on nylon standoffs at all five M3 holes—corners
> (4, 4), (42.3, 4), (4, 114.4), (42, 114.4) and mid-span (4, 64) mm—with the plate ≥ 3.5 mm below the bottom face
> (bottom parts hang up to 3.0 mm), non-conductive under the whole bottom face, and carries both SMA plugs with a
> tie or saddle at each plug's ferrule about 25–30 mm aft of the board edge; aft edge at joint ≥ + 80…83 with the
> loops off the shroud side, or ≥ + 91…95 with the loops forward of the shroud, fixed after the shroud's angular
> position is measured), eyebolt nut and charge wiring ~25, recovery ~260 (G10 forward bulkhead with forged
> eyebolt, three charge wells, Nomex, shock cord, 36″ chute). Leaves ~52–68 mm of slack depending on the shroud
> clearance. Recovery length is an estimate until the chute and cord are chosen.

Slack check: 595 − (80 + 44…48 + 118 + 25 + 260) = 64–68 mm with the loops off the shroud side. With the aft edge
at joint + 91…95 it is 550 − (91…95 + 118 + 25 + 260) = 52–56 mm (pass2_mechanical §3.6).

**Parent `CLAUDE.md` line 46.** It now reads "(SX1262 on SPI, 22 dBm, 900 MHz LoRa; E22-900M22S as the alternate)".
Proposed: "(SX1262 on SPI, 22 dBm, 900 MHz LoRa; the E22-900M22S is a layout alternate, 20 × 14 mm on a different
land, that needs a respin)". Commit it in the parent repository under its commit-often rule.

## 3. For the records agent (M3_R7, R7_VALIDATION, STATUS)

- **M3_R7:**
  - §DC solve, with the R7 values and board SHA from the F3 fix agent's rerun. F4 cites this section by name.
  - The R7 support-span/vibration estimate: method, inputs and results with the plugs on the jacks and with the
    plugs carried by the sled (pass2_mechanical §3.3), the owner's no-sixth-support decision, and a pointer to
    the ORDERING §5 tap/modal check.
  - A bay stack and orientation paragraph: y = 0 aft with the jacks, J1's entry toward y = 118, a pointer to
    ORDERING l.5 and §7 and to the REQUIREMENTS board position.
  - A pointer to MARGIN_PRESCRIPTION's R14 (R7) row.
  - Stitching gaps corrected to 4.27 / 3.68 mm and marked accepted (RF-03; also R7_VALIDATION and
    stepB_handoff).
  - The pin contract EXTI note (ELECTRICAL-03).
  - The D30 clamp trade-off and ESD handling rule in §"RF chains" (ELECTRICAL-04).
  - Q30 rise +30–40 K (ELECTRICAL-05).
  - DIO1 via 3.03 mm (REQUIREMENTS-13d).
  - Point the check_r7 strip comment at the F10 list or stepB_handoff §4 (REQUIREMENTS-05).
- **STATUS / R7_VALIDATION:**
  - Close the J2/NRST open item (decision above).
  - Close the LS120 reflow item (R7P1-13).
  - Close the F4 "not re-solved" item once M3_R7 §DC solve exists.
  - List the P2 vibration estimate as open until M3_R7 records it, and the bench tap/modal check as open.
  - Keep the board position open (Onshape shroud measurement).
  - Credit RF-net isolation to `check_r7` plus DRC/parity (REQUIREMENTS-11).
  - Record the forward-tab request or confirmation as a pre-order gate (DFM-03).

## 4. Not resolved here

- **REQUIREMENTS-09 / DFM-10 (antenna legends) were not in my list.** The board says GNSS on top and RADIO on the
  bottom, while ORDERING §7 still says to label the leads "GNSS and 915". Whoever settles the legend should
  align ORDERING §7.
- **Other bare NRST copper stays uncoated.** C24's NRST and GND pads are 0.34 mm apart, and U1 pin 14 is also
  bare. The decision covers only J2. The NRST gate measures the leak from all of them, which ORDERING §5 says.
- **The forward panel tab depends on JLC.** ORDERING makes it a written-confirmation gate before production. It
  is not a closed fact.
- **`tools/route_check.py` does not exist yet.** M2, R7 acceptance and ORDERING §1 name it ahead of the tools
  agent's work.
