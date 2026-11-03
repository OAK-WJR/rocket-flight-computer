# Round 18, documentation and firmware-binding consistency (Claude)

Target commit dcbb6c8, board SHA-256 632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982 (before = after).

**Totals: 0 Critical, 0 Major, 14 Minor.** All numbers I could check against the board (hash, size, counts, poses, pin map, IMU axis, silkscreen, cost, stock) are correct; the defects are duplication, readability and a few wording contradictions.

## R18-DOC-01 (Minor) Same ~48-line review-status block pasted into six files; AGENTS.md and the vehicle handoff carry it too

- Evidence: Identical block (starts 'Full R16/R17 pair complete'): STATUS.md 9-56, docs/M3_R10.md 3-50, docs/ORDERING.md 224-271, docs/R10_VEHICLE_HANDOFF.md 9-56, AGENTS.md 28-75, plus a variant in docs/R10_VALIDATION.md 3-45 and docs/REQUIREMENTS.md ~170-190. Drift already present: AGENTS.md line 22 says 'one new R16 integrated build/check0 matches both R15 snapshots' while the block says 'one complete R16 build/check0 matched both snapshots'; the first vehicle-facts table in R10_VEHICLE_HANDOFF.md does not start until line 60. AGENTS.md is the stable collaboration guide loaded every session via CLAUDE.md, yet ~50 of its 117 lines are round bookkeeping.
- Impact: Every status change must be made in six places and they will diverge; the owner and a vehicle integrator must read ~50 lines of review history before reaching the content they came for.
- Fix: Keep the full block only in STATUS.md (lines 9-56). In docs/M3_R10.md, docs/ORDERING.md section 8, docs/R10_VEHICLE_HANDOFF.md and AGENTS.md replace it with: 'Status: PCB 632a9ad3... (46 x 90 mm, unaccepted, unordered). Full status and the evidence list are in STATUS.md, section R10 candidate.' In R10_VEHICLE_HANDOFF.md move the terminal table (line 60) and the fit paragraphs to the top. In AGENTS.md delete lines 28-77 and keep only the section 1 table and the two links at lines 77-78.

## R18-DOC-02 (Minor) Numbers glued to words and units throughout the current-status text

- Evidence: Examples (exact text): STATUS.md 31 / M3_R10.md 25 / ORDERING.md 246 / HANDOFF.md 31: 'Final post-R17 canonical check: exit0.** All32rules,7shell/180R10/31fit/16paste/5parts/67route tests'. AGENTS.md 22: 'bound to632a9ad3:82 codes(46 Extended/36 Basic),199 fitted, orientation187 reconstructed+12 placement-only checks, paste245 top/373 bottom' and 'Supplier2026-10-30T17:15:34.705395..17:15:45.842149UTC:79.5232USD placed/81.8636USD minima'. R10_VALIDATION.md 1517-1530 and 1580-1612 (e.g. 'Camera bypasses', 'U9/R84 tolerance': 'Calculated3.946188..4.856999A from exact750ohm TI3.96..4.84A'). HANDOFF.md 84: 'height is1.0 mm +0/-0.10 ... At4 mm the allocated gap is2.9 mm'. pin_table.tsv rows 51,52,63,64,78-81: 'Direct UART through1k', 'R46010k to3V3' (reads as 'R460 10k to 3V3'). M3_R10.md 166-168: 'with0Critical/0Major/12consolidatedMinor groups'. About 130 glued tokens in AGENTS.md, 237 in STATUS.md, 365 in ORDERING.md, 745 in R10_VALIDATION.md.
- Impact: Values like 'R46010k' and 'exit0' cannot be searched or parsed reliably; the owner has to decode which part is the reference and which is the value. This is the main readability defect of the record.
- Fix: Mechanical fix: regenerate every affected line with a space between a letter/closing bracket and a following digit when the digit starts a number (regex ([A-Za-z\)])(\d) -> \1 \2, skipping hex hashes, reference designators like R46 and J400, and tokens such as AN2606, DS12110, TN1383). Rewrite the test-count sentence as: 'Final check after R17: exit 0; 32 rules; tests: 7 shell, 180 R10, 31 fit, 16 paste, 5 parts, 67 route; 4 NumPy skips resolved separately.' In pin_table.tsv use 'R460 (10 k) to 3V3'.

## R18-DOC-03 (Minor) AGENTS.md pin order for J410/J420 omits the 'board' perspective

- Evidence: AGENTS.md line 15: 'Pins1 supply,2 GND,3 TXO,4 RXI.' Board check: J410.3 = GPS_TX_WIRE is driven by U1.63 (PC6, USART6_TX) through R441; J420.3 = RADIO_TX_WIRE is driven by U1.52 (PB13) through R451, so legends TXO/RXI are the BOARD's, and a GPS module's TX must go to pin 4 RXI. docs/R10_VEHICLE_HANDOFF.md and docs/M3_R10.md 263 say 'board TXO / board RXI'; AGENTS.md line 14 for J9 says 'board RXI' but line 15 does not. J9 pin 3 is the board's RX, so the GPS/radio pair order is the reverse of the camera.
- Impact: A harness built from the AGENTS.md table alone can swap TX/RX on both GPS and radio.
- Fix: AGENTS.md line 15: replace 'Pins1 supply,2 GND,3 TXO,4 RXI.' with 'Pins: 1 supply, 2 GND, 3 board TXO (board transmits; wire to the module RX), 4 board RXI (wire to the module TX). The camera port J9 is the reverse: 3 board RXI, 4 board TXO.'

## R18-DOC-04 (Minor) J121 contact names differ between docs and silkscreen

- Evidence: Board silkscreen: '1:E1-' and '2:E1+' (text at (8.8,49.8) and (8.6,60.4)) with word 'IGN'. AGENTS.md line 18, R10_VEHICLE_HANDOFF.md terminal table and R10_VALIDATION use 'OUT / IGN' only. Only ORDERING.md line 406 maps 'E1-/PYRO1_OUT, E1+/PYRO1_IGN'. Nets verified: J121.1 = PYRO1_OUT, J121.2 = PYRO1_IGN.
- Impact: A person reading the board sees E1+/E1-, a person reading the handoff sees OUT/IGN; the e-match polarity convention is not stated where the harness is specified.
- Fix: AGENTS.md 18 and HANDOFF.md table: write 'pin 1 OUT (silk E1-), pin 2 IGN (silk E1+)'.

## R18-DOC-05 (Minor) The cost headline hides the all-in figure, and the $84.41 target is never defined where it is used

- Evidence: STATUS.md 37-41, M3_R10.md, ORDERING.md 8.1, HANDOFF.md, AGENTS.md 22 and R10_VALIDATION.md section 10 all say '$79.5232 ... below $84.41 before fixed/process/PCB/shipping costs'. The definition (R3's per-board cost, REQUIREMENTS.md M3, line 146) appears only in REQUIREMENTS.md. fab/cost_check.json holds fixed_fees_usd_per_order 83.96 and handling_fee_may_apply_usd 14.93, i.e. +$16.79/board (+$2.99 if handling applies) at 5 boards. Numbers verified against cost_check.json and stock_check.json: 79.52 / 56.77+25.092 = 81.8636, R430 17<3610, U4 0<5, U9 83/min 7 (+$0.5382/board), 82 codes, 46 Extended.
- Impact: 'Cost target passes' reads as 'the board is affordable'; the order-day number is about $96-99 per board before PCB, rails, VIPPO, C84 manual fit, consignment, shipping and tax.
- Fix: In the Procurement paragraph add: 'The $84.41 cap is R3's per-board cost (REQUIREMENTS M3) and counts parts plus feeder fees only. Adding JLC fixed fees ($83.96/order = $16.79/board; possible handling $14.93 = $2.99/board) gives about $96.3 (to $99.3) per board before PCB, shipping and tax.'

## R18-DOC-06 (Minor) 'R10 deviations for owner acceptance' has no list of the decisions the owner must make

- Evidence: docs/R10_VALIDATION.md 1516-1877: a 2-line preface (1516-1529) then 13 prose/table sections (~350 lines). The decisions are scattered: unfused battery and no physical break while powered (section 1), servo return share <=0.6144 A inference (2), shared-fault loss of both GPS/radio ports (3), hold-up 0.49-0.57 ms with ports on (4), pyro ADC single-fault pin damage (section 5 paragraph: PA6 can see 8.4 V against a 4.0 V ADC ceiling; PB1 can approach 5.456 V through 10 k after an open bottom resistor), routing M2 compromises (6), MEMS stress departure (HANDOFF only), DB125 insertion / S-8 0.1025 mm margin (1, 9), cost and stock (10). The two single-fault ADC pin-damage cases are the least visible and are not mentioned in STATUS.md, AGENTS.md or the handoff.
- Impact: The owner cannot accept or reject a list she cannot see as a list; a hardware pin-damage fault is buried mid-paragraph.
- Fix: Insert at line 1530 a table 'Decision | What you accept | Consequence if wrong | Closure test | Section' with these rows: 1 single switch, unfused battery, no break while powered; 2 servo return through shared GND; 3 always-on GPS/radio, one cable fault drops both; 4 hold-up 0.49-0.57 ms (ports on); 5 PA6 and PB1 single-fault pin damage; 6 e-match 20 ms firing and 36 ms watchdog guard unproven on the lot; 7 routing M2 compromises and TN1383 MEMS departure; 8 DB125 insertion and S-8 margin 0.1025 mm; 9 cost and stock (R430, U4). Keep sections 1-13 as the supporting detail.

## R18-DOC-07 (Minor) Camera-energy increment quoted in ORDERING.md does not match the table beside it

- Evidence: docs/ORDERING.md 344: 'The nominal 5.456 V, 6 V/80% extra 1.5 h camera term is 1.705 Ah.' The table above it (8.1.1) gives 4.123602 - 2.390393 = 1.733209 Ah for the same 1.5 h, because the table uses the 5.546269 V upper allocation. 1.5 h x 5.456 V / 0.8 / 6 V = 1.705 Ah, so the sentence is correct for its stated basis but silently uses a different voltage.
- Impact: A reader checking the table finds a 0.028 Ah mismatch.
- Fix: Replace with: 'On the table's 5.546 V basis the extra 1.5 h of camera is 1.733 Ah; at the nominal 5.456 V it would be 1.705 Ah. Use 1.733 Ah.'

## R18-DOC-08 (Minor) Same facts cited to different datasheet revisions

- Evidence: r10_binding_note.json firmware_obligations: 'GPS USART6 PC6 TX/PC7 RX AF7 (DS12110 Rev10 Table12 p91); radio UART5 ... (Table11 p90)' versus pin_table.tsv rows 63-64: 'DS12110 Rev11 Table9 p79 ... Table10 p92 AF'. AN2606: pin_table.tsv and binding use 'AN2606 Rev64 Table119 pp277-280', while M3_R10.md, ORDERING.md, HANDOFF and R10_VALIDATION (section 5) use 'AN2606 Rev70 Table2 Pattern10'.
- Impact: Page and table numbers change between revisions; a reader cannot tell which PDF to open (AGENTS section 3 'verify, don't guess' needs one source).
- Fix: Pick one revision per document and name its URL once. If both AN2606 revisions are intended, add to the binding note: 'Table119 roles from Rev64; boot-mode patterns from Rev70.' Update the binding note's Rev10 cites to the Rev11 table numbers used in pin_table.tsv.

## R18-DOC-09 (Minor) Net name ARM1_SENSE conflicts with the 'sole RAW_ACT sense' wording

- Evidence: AGENTS.md 18: 'RAW_ACT is behind Q120/Q121 ... directly feed PC0/PC5'; AGENTS.md 12: 'sole RAW_ACT sense PC5'. pin_table.tsv row 33 names PC5 ARM1_SENSE; M3_R10.md says it 'measures the post-load-switch bus; it does not witness a physical ARM link'. J124 and any ARM link no longer exist.
- Impact: The name suggests an ARM-link state, which R10 does not have; an AGENTS section 2 reader may think arming is sensed.
- Fix: AGENTS.md 12: 'sole RAW_ACT bus sense PC5 (net ARM1_SENSE, a name kept from R9; it senses the post-load-switch bus, not an ARM link)'. Same note in pin_table.tsv row 33 reset_contract column.

## R18-DOC-10 (Minor) M3_R10.md placement paragraph is an unreadable review changelog with unexplained tokens

- Evidence: docs/M3_R10.md 163-168: 'Full R13 then reviewed7355/fa897c8 with0Critical/0Major/17Minor groups ... R15 reviewed the R14 fix PCB7866d6b8 ... Full R16 reviewed632a9ad3'. '7355' is the board hash prefix 7355ae1a (R10_VALIDATION 939) printed without a trailing ellipsis; '7866d6b8' and 'e0e3ad84' are unexplained.
- Impact: A design-record section about placement contains round history in one 900-character line.
- Fix: Replace lines 165-168 with: 'Placement history: R11 found that the terminal envelope omitted a tolerance corner, so both terminal rows moved inward 0.40 mm. Rounds 12 to 17 reviewed the result (table in R10_VALIDATION.md, Review-round log). The AVA hand-off measurements are historical evidence for board 0c50b9fd.' Delete the round-by-round counts.

## R18-DOC-11 (Minor) STATUS.md R10 section lacks the facts a reader needs and carries nine superseded bullets before them

- Evidence: STATUS.md 9-57 current status; lines 64-73 are nine bullets about boards 6e73b6ea, b337fe63, 877d0199, 73af96b and b860afbe, including line 73 'What changed from R9 (as of b337fe63...)' that still describes 'GH-4 ports with translators and switched, current-limited supplies' and 'J1 split (battery terminal + GH-2 switch)'. The current R10 block has no IMU axis map (roll = -gyro_Y, lever arm x = -6 mm, z = -2.06 mm Inference), no terminal pin table and no pin-map pointer; those appear only in AGENTS.md and r10_binding_note.json. Verified against the board: U4 B(17,45.9) rot 180, axis x = 23, J-positions, 209/951/296/168 GND, 2,256,162 bytes, 1788.675665 mm, 118 visible + 91 hidden references, 40 silkscreen texts, 82 BOM codes, 199 CPL rows (67 top, 132 bottom), five round-edge supports; all match the docs.
- Impact: Numbers are correct but the superseded text is easy to mistake for current (the GH/translator wording contradicts the board).
- Fix: Move STATUS.md lines 64-73 to docs/HISTORY.md under 'R10 interim boards'. Add under the current block: 'IMU: U4 bottom, rotation 180; roll = -gyro_Y; lever arm x = -6 mm, z = -2.06 mm (Inference). Pin map: sources/r10_design/pin_table.tsv (r10_net column). Terminals: see the table in docs/R10_VEHICLE_HANDOFF.md.'

## R18-DOC-12 (Minor) ORDERING.md section 7 still lists R9 harness items (ARM link with 5 A fuse, 15 A battery fuse) that R10 deliberately omits

- Evidence: docs/ORDERING.md 200-215: 'Arming link ... black ARM terminal J124 with a 5 A fast-acting 5 x 20 fuse' (line 204), 'Battery lead (R9) In-line 15 A ATO fuse' (206), igniter row (205) for the R9 terminal. Section 8 line 219 says sections 1-7 describe R9, but section 8.4 'Battery lead: No battery-lead fuse/holder (OQ-6)' is the R10 rule. J124 does not exist on the board.
- Impact: A harness builder reading section 7 would add an ARM link and a fuse that the R10 design does not have, or conclude R10 requires the 15 A fuse.
- Fix: Add 'R9 only' as the first word of each row in section 7, or move rows 204-206 under a heading '7 (R9 only)', and add at the top of section 7: 'For R10 use section 8.4.'

## R18-DOC-13 (Minor) AGENTS.md table rows mix R7/R8/R9 history with R10 facts and contain stale statements

- Evidence: AGENTS.md 11-22: each cell is 1.7-2.8 kB (line 22: 2,795 characters; R10 text starts at the bold marker near the end). Line 18 still reads 'plus 4.7 kohm at each ADC pin (R168, R170, R172)': R168, R170 and R172 are not on the board (pad scan), and the same row's R10 text says 'no redundant bank/ADC tails'. Line 16 and others cite J30/J31/U30/U31/J123/J124, absent from R10. The 12-ID suffix '(D-AVA-01/D-R11-01/.../D-R17-01...04)' is repeated 12 times and never explained.
- Impact: Stale component references and unexplained decision-ID lists make the table hard to act on; a reader may think R172 and the 4.7 k tails exist.
- Fix: Rewrite section 1 as a table with columns Function | Current R10 design (one sentence, pin map or position) | Where verified. Delete the R7/R8/R9 history from the cells (it exists in M3_R7/R8/R9.md). Replace the repeated ID list with 'D-xx IDs are in sources/r10_design/R10_DECISIONS.md'.

## R18-DOC-14 (Minor) 'The same-PCB clean pair is earned' states a process outcome without saying who reviewed

- Evidence: STATUS.md 18-21, M3_R10.md 12-14, HANDOFF.md 18-21 and similar: 'The same-PCB clean pair is earned.' Rounds 1-17 were all done by one model family; REQUIREMENTS says the clean pair gates ordering. Round 18 is the first reviewer from another family.
- Impact: Without the qualifier an owner may treat 'earned' as independent confirmation.
- Fix: Replace with: 'Two consecutive reviews (R16, R17, same reviewer family) found no Critical or Major issue on this PCB. Round 18 is the first review by a different model family.' Do not otherwise change the AGENTS section 2 text.

## Verified consistent

- Board hash, size, bytes, footprint/segment/via/GND-via counts, track length: all documents match the board (632a9ad3..., 46 x 90 mm, 2,256,162 bytes, 209/951/296/168, 1788.675665 mm).
- U1 all 100 pin nets: board, pin_table.tsv r10_net and r10_binding_note.json u1_pins agree (0 mismatches); pin_table_sha256 56b7734a... matches the file; binding note sha 35bb0629... and fab hashes match round17_fix_validation.json.
- Positions in AGENTS.md (J1, J400, J121, J9, J410, J420, J122, U1, U4, U5, U9, R166, LS120) and the five support holes match the board.
- IMU axis map: binding roll = -gyro_Y, lever arm x = -6 mm matches U4 x = 17 against axis x = 23.
- Silkscreen: 118 visible / 91 hidden references and the hidden list in M3_R10.md match the board exactly; 40 texts and all 23 terminal pin legends exist.
- Cost/stock: cost_check.json and stock_check.json match every quoted figure (79.5232, 81.8636, 82 codes, 46 Extended, R430 17<3610, U4 0<5, U9 83/7, +0.5382); pad-energy table arithmetic checked.
- BOM/CPL counts: 82 BOM codes, 199 CPL rows (67 top + 132 bottom) = 187 + 12.
- Fire timing numbers (32.653 + 0.2 + 0.5 + 1.5 = 34.853 ms; 35.797 W x 36 ms = 1.2887 J) consistent.
- D-ID (126) and owner-mandate (23) counts match r10_final_deviations.json.
- All relative markdown links in the six files resolve.
- AGENTS section 2.5: no inference found written as fact in the current-status text; labels (Inference, Calculation, conditional) are present.

## Coverage limits

- Datasheet page numbers in pin_table.tsv were not re-opened (other lenses); only internal consistency between documents was checked.
- R10_VALIDATION.md rounds 3-15 (historical) read only as far as needed; not every historical line was checked for staleness.
- Netlist and circuit hashes in the binding note were not recomputed (needs a netlist export).
- Log files cited by round17_fix_validation.json were not opened.
