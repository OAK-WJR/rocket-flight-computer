# Round 19 - requirements and physics roots (Claude)

Target commit 1e60441; board SHA-256 a3144b15... unchanged before and after.

Totals: 0 Critical / 0 Major / 10 Minor. Every AGENTS section 2 rule and the owner single-switch, AUD, GAP and connector decisions trace to the board; no requirement is contradicted by hardware, and no removed hardware remains on the board or schematic. Findings are stale text, margins without a flight root, and one failsafe conflict that is disclosed as an accepted risk but has a cheap physical remedy.

## R19-REQ-01 (Minor, carried (R18-REQ-05)): Pad-energy worksheet stacks four unrooted margins; the pack it implies is about 3x the physics-supported size

Evidence: docs/ORDERING.md 8.1.1 and round17_pad_energy.json: board input 5.437970 W = 0.461 A x 5.546 V / 0.8 (3.196 W ports) + 1.4 W logic + 0.825 W continuous SD write + 0.017 W; 2 h at a 6 V charge basis = 1.8127 Ah, 2.2658 Ah after the 20 % reserve. (a) 0.461 A has no stated source anywhere in the repo (grep: only ORDERING 8.1.1, R10_DECISIONS D-R17-01 and the json); REQUIREMENTS Pack row itself gives the ports as about 1.7 W (LR900-F 1 W maker average + GPS 0.05 A, 85 % buck) - the worksheet carries 3.196 W for the same loads. (b) SD write on the pad: F5 logs from launch with a RAM ring buffer, so pad SD power is about 0 W (0.825 W charged for 2 h = 0.275 Ah). (c) 1.4 W logic against REQUIREMENTS Temperature row: firmware runs at 200 MHz; the same row quotes 0.4-1.1 W at 480 MHz, so about 0.17-0.46 W at 200 MHz by dynamic-power scaling (Inference). (d) Wh is converted to Ah at 6 V (2 x 3.0 V, the empty end of the discharge curve), but rated Ah is delivered over the whole curve (about 7.4 V nominal): 10.88 Wh / 7.4 V = 1.47 Ah, not 1.81 Ah. Re-based on the Pack row figures (1.7 W ports + about 0.5 W logic + 0.02 W, 2 h, 7.4 V nominal) the board pad charge is about 0.6 Ah, 0.75 Ah with the 20 % reserve (Inference; arithmetic in the report text). The worksheet text (ORDERING 8.1.1, last paragraph) acknowledges (b) and (c) and keeps the larger numbers "until the owner asks".

Impact: The pack is the largest single volume in the main section (about 80 mm battery bay, 50.8 mm bore). A 2.27-5.15 Ah board-only requirement, before motors, flight and recovery are added and divided by 0.8, probably cannot be met inside that bay (pack dimensions not verified here), and it is a margin stack, not a flight need. The two-hour pad wait itself is an owner-stated assumption and is kept.

Fix: Reissue the worksheet on one honest basis: ports from the Pack row (or the maker current of the LR900-F in idle/telemetry mode, cited), SD = 0 W on the pad and 0.825 W only from launch to apogee+30 s, logic from the 200 MHz power in parts_budget.json, Ah = Wh / 7.4 V (or Wh / nominal pack voltage of the chosen cell), and keep the single 0.8 usable-capacity factor. Records only, no board change.

## R19-REQ-02 (Minor, new (extends R18-REQ-12)): The inherited switch-bounce network delays recovery after a real power loss to 0.4-1.1 s, against the owner failsafe of a neutral command within 50 ms

Evidence: docs/REQUIREMENTS.md F6 and Accepted risks: reboot after a brownout longer than the ride-through "about 1.1 s"; battery_entry.kicad_sch note on C87: (R80+R165)||R81 = 227 kohm charges C87 2.2 uF, so turn-on takes 0.4-1.1 s, and bounce shorter than 0.11/0.21/0.27 s at 6.0/7.4/8.4 V cannot trip U9. R10_DECISIONS "Owner questions closed by physics" (GAP list): "neutral quickly" = neutral PWM within 50 ms; F6 Reset/startup allocation <= 48.653 ms. REQUIREMENTS Flight table: stuck-tab roll estimate about 1100 deg/s. Board: C87 is 2.2 uF 16 V X5R (C23630, shared code with C19/C20), R81 300 kohm. R18-REQ-12 added a bench acceptance of "longest contact drop-out < 10 ms", which a time constant of about 0.1 uF x 300 kohm = 30 ms already covers.

Impact: The owner failsafe (tab back to neutral quickly after reset/hang/brownout) is met by the IWDG path but not after a supply interruption longer than about 0.2 s (loose screw, a real battery break): U9 turns off, and recovery waits 0.4-1.1 s for C87 to recharge before boot even starts. That is about the time a stuck tab needs to spin the vehicle up. The 0.15 s immunity it buys has no measured root (R18-REQ-12) and the proposed acceptance (10 ms) needs one tenth of it.

Fix: Owner/bench decision, not a fix-now: after the contact-chatter measurement, set C87 from the measured longest drop-out (physics supports about 0.1-0.22 uF: R81 x C87 = 30-66 ms discharge and a 0.02-0.1 s turn-on). C14663 100 nF 0603 is already a stocked code, so the 2.2 uF line drops from 3 to 2 parts and no code is added. Update F6 and the Accepted-risks 1.1 s line to match. Keep the board as it is until the measurement exists.

## R19-REQ-03 (Minor, new): docs/M3_ACTUATOR_MERGE.md is cited as a current source but describes removed hardware and has no superseded banner

Evidence: AGENTS.md section 1 table rows "Actuator power switch" and "Shorted-igniter current limit" cite docs/M3_ACTUATOR_MERGE.md (and section 2.6); REQUIREMENTS F7 and F8 cite it. The file (status "design + CAD only", 2026-09-25 R2) describes: two independent pyro channels each with its own fused bus; Q120/Q121 AON6403 C2760089 (board has AONR21357 C431196); 7.7 A actuator rail with servo header; R122/R123 100k/100k from RAW_PROTECTED (board: R122 1 kohm from PC1, R123 2 kohm); C121 470 uF on RAW_ACT (absent); RAW_ACT sense R124/R125 to PB0 (absent); in-line 15 A fuse; launch pull-pin (J123, removed); the ARM terminal (J124, removed). Only section 2.6 survives. The first line has no banner (head -25 read).

Impact: AGENTS section 1 sends reviewers to it for the Q120/Q121 and R134 design; a reader who follows the link meets the opposite of the single-switch, off-board-servo design (for example, "the actuator rail is on only when the U9 logic path is on", "servo header").

Fix: Add a one-line banner at the top: "Historical R2 record. Current for R10: section 2.6 (shorted-igniter limit) only; everything else is superseded by R10_DECISIONS single-switch, AUD-3/4/6 and D-R18-01/02." In AGENTS rows, cite "M3_ACTUATOR_MERGE.md section 2.6" only for the R134 limit and point the Q120/Q121 row to M3_R10.md "Power". Text only.

## R19-REQ-04 (Minor, new): FMEA_REDUNDANCY.md row I-7 still states the Q122 pull-down R123 = 100 kohm after D-R18-01 made it 2 kohm

Evidence: docs/FMEA_REDUNDANCY.md line 39 (I-7; F-6 / F-10 / F-16): "drives ACT_EN_MCU through R122 1 kohm into Q122 with R123 100 kohm pull-down". Board R123 = 2k (C4109, pcbnew value 2k, nets ACT_EN / GND); BOM m3_bom_jlc.csv "2k ... R123,R130,R180"; D-R18-01. docs/M3_R10.md lines 42, 102, 176 and 576-578 are updated, and M3_R10.md 708 is a labelled history entry. The FMEA is the safety record the arming argument (AGENTS 2.4) cites.

Impact: The FMEA row for the load-switch enable cites the value that D-R18-01 changed because the 100 kohm did not dominate a PC1 internal pull-up (gate 2.19-2.52 V against a 1.45 V maximum threshold). A reader assessing I-7 reads the pre-fix circuit.

Fix: Replace "R123 100 kohm" with "R123 2 kohm (D-R18-01: gate <= 0.220 V against a 30 kohm PC1 pull-up at 3.6 V)" in FMEA line 39 and any other FMEA row that restates the value. Text only.

## R19-REQ-05 (Minor, new): REQUIREMENTS F9 has five run-together words, one of which hides a component value

Evidence: docs/REQUIREMENTS.md F9: "exactR923.3 kΩ/R1660.36 Ω" (R92 3.3 kΩ and R166 0.36 Ω; as written R92 reads as 23.3 kΩ), "harnessR ≥ 0.03 Ω", "confirmTP80<1 V", "bothGPS/radio", "bothU9 IN and OUT", "Pack change:e-match". Board: R92 value 3.3k (BOM line "3.3k 1% R92"), parts_budget R92_resistance_min 3234 ohm.

Impact: The value of a safety-relevant part (the logic-path bleed in the hot-plug model) can be misread; the same lost spaces show the F9 row was edited by automated replacement.

Fix: Restore the spaces: "exact R92 3.3 kΩ / R166 0.36 Ω", "harness R", "confirm TP80", "both GPS/radio", "both U9". Text only.

## R19-REQ-06 (Minor, carried (R18-REQ-06)): P3 keeps a 500 g-equivalent (5 x 100 g) retention load with a basis that names no flight number for it

Evidence: docs/REQUIREMENTS.md P3 (post-fix text): 100 g design load is "close to the 92 g landing case of DESIGN_ASSURANCE 6.1"; boost loads 28-37 g (flight table); "the parent VEHICLE.md gives no ejection g figure, so the 500 g equivalent stays until it is measured or replaced by the owner". Retention is open, "not passed by inspection".

Impact: The fix pass only recorded the basis; the 5x factor over the largest stated load (about 2.7x the 37 g peak is already in the 100 g) remains a margin that every release carries as open and that drives staking and standoff rework.

Fix: Owner choice: restate P3 as 100 g design load with a retention factor of 2 (200 g equivalent) for C84, DB125 bodies, J3 shell and LS120, or give the ejection/shock-cord snatch figure that needs more. Text and first-article pull/mass test only.

## R19-REQ-07 (Minor, new): C84 hold-up (470 uF, hand-fitted) has no derived required duration, and its 0.49-0.57 ms ports-on figure is shorter than the actions the text names

Evidence: REQUIREMENTS F6: hold-up to 3.8 V at 300.8 uF is 0.490-0.571 ms with all ports and the card writing (1.533-1.655 ms camera off/logic shed); OQ-5 in R10_DECISIONS: "do whatever AVA does", no hold-up time derived. No document states the time the logic must stay alive. Winbond W25Q128JV tPP (page program) 0.4 ms typical, 3 ms maximum (datasheet AC table, cached copy line "Page Program Time tPP 0.4 3 ms"); TPS2553 turn-off up to 3 ms (R10_DECISIONS Always-on ports, same text). F6 itself forbids a blocking flush on sag. The cost: C84 is an 8 x 10 mm polymer part with no maker reflow profile, so it is excluded from the JLC upload and hand-fitted after both reflows (D-R18-09), plus a C84 staking and retention item in P3.

Impact: With no stated need, the 470 uF cannot be judged oversized or adequate. It is too short to finish one QSPI page program (3 ms) with the ports on, and the only action that fits (PA6 analog watchdog interrupt, stop writes, lower camera OE: tens of microseconds to under 0.2 ms) needs far less than 470 uF. The part costs a manual assembly step, a height/ESR first-article check and a retention item.

Fix: Record the hold-up requirement as a time: the interval the firmware needs after the PA6 watchdog fires (measure on the bench: ADC watchdog latency + shed sequence). If it is about 0.2 ms, 100-220 uF satisfies it and the capacitor can be a reflow-rated part with a maker profile; if the intent is one QSPI page (3 ms), 470 uF is not enough with the ports on and the text should say so. Owner decision (OQ-5 is an owner mandate); no board change now.

## R19-REQ-08 (Minor, carried (R18-REQ-03, partly fixed)): About 35 % of REQUIREMENTS.md is still R7-R9 acceptance and cost history inside current rows

Evidence: docs/REQUIREMENTS.md (committed): total 55,924 characters; row M2 10,896; row M3 5,475; the three sections "R7 acceptance", "R8 acceptance", "R9 acceptance" 3,252; together about 19.6 k (35 %). Row M2 still carries the R7-R9 deviation-list acceptance narrative (hashes c872a3d3, cc044ea0, 4f841a0e), the R8 D10 detour amendment and the R7/R8/R9 cost snapshots in M3. The fix pass removed the stale hardware clauses from M1, P1, Pack, Camera and Accepted-risks rows (verified) but not these.

Impact: The current R10 requirement in M2 and M3 has to be found inside historical numbers; a single-sentence R10 rule is buried in 11 k characters.

Fix: Move the R7-R9 acceptance sections, M2 history after "R10:" and M3 cost snapshots to docs/HISTORY.md or the matching M3_R* file; leave one R10 paragraph per row. Text only.

## R19-REQ-09 (Minor, carried (R18-REQ-04)): Parent docs/VEHICLE.md main-section stack row still describes the R9 and old R10 connectors

Evidence: ../../docs/VEHICLE.md "Main-section stack" row (read at the committed parent state): "battery leads and RF coax loop zone ~44-48 (two straight SMA plugs...)", "GH-4 ports on the x = 46 edge", "battery terminal and ARM / IGN terminals on the x = 0 edge", "GH-2 power-switch connector J400 near the forward edge at (10.5, 85.5)", "GH ports mated 0.03 mm inside the bore". Board: J400 DB125-2 at (7.4, 65.85), J1 (7.4, 75.85), J121 (7.4, 55.85), J410/J420/J9/J122 at x = 38.6, y 15.5/31.5/47.5/71.5; no coax, no ARM terminal.

Impact: The OQ-7 stack arithmetic (aft edge joint + 79-83 mm, margin to the joint + 47 mm shroud limit) uses a lead zone that includes the removed coax loops, so the margin is conservative; the vehicle record names connectors that do not exist. The parent repository is outside this worktree.

Fix: In the parent repo replace the R10 clause with the terminal table from docs/R10_VEHICLE_HANDOFF.md and restate the lead zone as battery leads only (about 25 mm bend allowance), re-deriving joint + 79-83 mm.

## R19-REQ-10 (Minor, carried (R18-REQ-07)): Gate still treats the 115200-baud port UARTs as fast interfaces and keeps dead RF and sense classes

Evidence: tools/critical_reference.py R10_SLOW_RETURN_NETS (committed) = {VLOGIC_SENSE, V3V3_SENSE, CAM_5V_SENSE, ACT_*, PYRO1_CONT, ARM1_SENSE (+_MID), CAM_PWR_EN/FAULT_N/UART_OE}: V3V3_SENSE was removed by D-R18-01 (no such net on the board, pcbnew), yet the entry stays with no stale-entry failure; GPS_/RADIO_/CAM_ UART nets are not listed so tools/route_check.py applies the 1.5 mm GND-partner-via and one-reference-region rules to 1 kohm-series, ground-ESD, multi-cm-wire UARTs at 115200 baud or less (rise time set by 1 kohm x pin and ESD capacitance, tens of ns, versus a layer-change return discontinuity below 1 ns).

Impact: A redundant constraint: partner vias and In2 region cuts around slow port UARTs, with no physical return-path root at that edge rate. No AGENTS section 2 effect.

Fix: Add the GPS/RADIO/CAM UART nets to R10_SLOW_RETURN_NETS under AUD-2 (keep their hygiene classes), drop V3V3_SENSE and the dead rfif / RADIO_SCK entries, make stale entries fail. Gate-only; do not alter the frozen board.

## Fix verification

- D-R18-01: R123 100 kohm -> 2 kohm C4109; R62/R63 (V3V3_SENSE) removed; PC3_C NC Result: confirmed (board and gate records); FMEA text partly (Board R123 value 2k, nets ACT_EN/GND; BOM "2k ... R123,R130,R180" qty 5 (pcbnew); no R62/R63 footprint among 208; U1 pad nets match pin_table.tsv r10_net on all 100 rows (0 mismatches), PC3_C NC; REQUIREMENTS F11 and M3_R10 updated. Stale value remains in FMEA row I-7 (R19-REQ-04).)
- D-R18-09 / R18-REQ-10 / R18-REQ-11: R430 stocked FOJAN C2999509; C84 owner-BOM only Result: confirmed (m3_bom_jlc.csv R430 22.6k 1% C2999509 FRC0603F2262TS; no C84 row in the JLC BOM or CPL; m3_bom_owner.csv C84 "manual, after both reflow passes"; CPL 197 rows, BOM 81 lines; stock_check.json short list = U4 only (0 < 5, consigned per M1); cost_check.json total 79.12 per board, 81 charged codes, ok true against the 84.41 target.)
- D-R18-10 / R18-REQ-01 / R18-REQ-02: MCU, battery and footprint-filter text corrected Result: confirmed (mcu.kicad_sch now reads CAM_PWR_EN PE11/pin41, CAM_FAULT_N PE12/pin42; no "0.33 ohm", "RADIO_SCK" or "GHS_TBT" string remains in any .kicad_sch.)
- R18-REQ-03: Removed-hardware clauses moved out of current rows Result: partly (REQUIREMENTS Sources, P1, M1, Pack, Camera, Pad arming and Accepted-risks rows are R10-clean. M2, M3 and the R7-R9 acceptance sections still hold about 19.6 k characters of history (R19-REQ-08); FMEA and M3_ACTUATOR_MERGE stale text (R19-REQ-03/04).)
- R18-REQ-05: Pack-size statements unified Result: partly (Pack row now defers to ORDERING 8.1.1 (confirmed); the worksheet still carries the 0.461 A / continuous SD / 1.4 W / 6 V stack (R19-REQ-01).)
- R18-REQ-06: P3 basis recorded Result: partly (recorded, not resolved) (Basis sentence present; 500 g equivalent retained (R19-REQ-06).)
- R18-REQ-08: F11 added; V3V3_SENSE removed; buzzer cold end restated Result: confirmed (F11 present with LED1/2, LS120, USB-C and PB1 diagnostic; Temperature row states the site limit and names the buzzer as the only part under -40 C.)
- R18-REQ-09 / R18-REQ-12: microSD and switch-bounce rooted Result: confirmed (F5 now states the owner-chosen convenience log, 2 MB vs 16 MB, and the deletion list; F6 labels 0.15 s as inherited and adds the < 10 ms bench acceptance. Consequence for the failsafe in R19-REQ-02.)

## Fix now

None. Every finding is text, a gate list, or an owner/bench decision; the frozen board needs no change.

## Closed candidates

- Q120/Q121 back-to-back pair is redundant now that servo power is off the board: Q121 (drain RAW_ACT, source common) is the forward-blocking FET; Q120 (drain BAT_IN) blocks reverse. Without Q120 a reversed pack would drive RAW_ACT negative through the Q121 body diode and put about -0.7 V on the ARM1_SENSE divider (PC5 injection). The pair is rooted in the accepted reverse-pack case and costs one 3 x 3 mm part; closed.
- U401 4.8 V LDO after the 5.3 V buck is an unnecessary stage: D-R1-03: camera needs at least 5 V, the radio maker specifies 4.5-5 V, one adjustable rail cannot guarantee both; physical root.
- Camera U12/U13/U402 isolation vs direct GPS/radio UARTs: The camera is the only switched supply (camera off on the pad, D-CIR-02); a powered MCU pin through 1 kohm into an unpowered camera is a state GPS/radio never have. Owner condition in the always-on-ports decision satisfied.
- Dual 5.1k/2k divider banks on PC0/PC5: Rooted in FMEA I-9: a single shorted top puts hundreds of mA-class current into the igniter path or the MCU pin; tolerance of one shorted/open part is the stated requirement.
- 0.1 % resistors R82, R83, R84, R86: OVLO 1.20 V +/-1.9 % and ILIM +/-10 % for ILIM > 1 A (TPS25947 datasheet p.1 and electrical table) dominate; OV threshold 9.77 V typical, 9.5-10.1 V with 1 % resistors, still above 8.7 V (LiHV) and below 12.6 V. Cost is under $0.2 per board and no space or routing effect; not worth a finding. R400-R403 (buck feedback, 5.03 V camera minimum) are justified.
- BAT_IN 1.0 mm copper (35.2 mm total) and 0.5 mm fire copper: Logic-path peak about 1.3 A (all ports on) needs about 0.55 mm at 10 K rise (IPC-2152, Inference); 1.0 mm is about 2x that but the length is short and AUD-6 already cut the fire-only copper to 0.5 mm. No routing benefit now that the board is routed.
- F3 barometer 10 km, F2 +/-64 g, F1 +/-4000 dps: Free margins from the single part choice (MS5611, LSM6DSV320X). 37 g peak axial and an uncontrolled-roll scaling of 1000-1850 deg/s to Mach 1.9 give about 1300-2400 deg/s, still above +/-2000 dps, so +/-4000 dps is the next available range.
- Removed hardware present on the board or schematic sheets: pcbnew listing of 208 footprints: no J123/J124, SMA, U410/U420/U411/U421/U412/U422, R62/R63; schematic sheet titles and notes mention them only as removed.
- Pin table vs board (R10 pin map): All 100 pad nets of U1 agree with pin_table.tsv r10_net.
- Support geometry and 3.8 mm washer claim (P2): Support centres (4,4), (42,4), (4,44.3), (3.7,86), (42,86) match; J2.1, J2.3, LED1.1 are 4.27, 4.38, 4.44 mm from (4,44.3) centre to pad centre.

## Coverage limits

- CAD-only lens: Bench and Flight rows (F1, F5 latency, F6 timing, F7 firing, F9 hot-plug waveforms, P2/P3 fit and vibration) cannot be verified here and remain open as the documents say.
- The 0.6 Ah figure in R19-REQ-01 is Inference from the documents own power figures, not a measurement; pack dimensions were not checked.
- Datasheet values taken from cached PDFs; the Winbond URL was not re-fetched. LR900-F and M100 Mini supply ranges rely on R10_DECISIONS D-R1-03.
- Hold-up and EN-network timings are the documents calculations; no simulation was run.
