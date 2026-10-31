# Round 18 fix pass: documentation lane (hand-back)

Scope: `STATUS.md`, `AGENTS.md` (section 1 table and the single-switch scope paragraph; section 3 routing bullet only; section 2 is byte-identical), `docs/REQUIREMENTS.md`, `docs/ORDERING.md`, `docs/M3_R10.md`,
`docs/R10_VEHICLE_HANDOFF.md`, `docs/R10_VALIDATION.md` and `m3_design/assembly_review/sources/r10_design/parts_qualification.md`. The first pass (before the CAD pass) described the board as it was reviewed (`632a9ad3…`); the second pass, "Reconcile after the CAD pass" at the end, brought them to the final board `a3144b15…`. Where a number in the first-pass tables below differs from the current documents, the documents and the last section govern. Nothing else was touched; no git state was changed.

## Structure of the result

- **One canonical current-state block:** `docs/M3_R10.md`, "Current state" (board table, review table, checks, simulation, cost and stock with the $84.41 target defined, retained deviations, not verified, datasheet revisions, evidence). `STATUS.md`, `AGENTS.md`, `docs/ORDERING.md` section 8, the handoff,
  `docs/REQUIREMENTS.md` (R10 acceptance) and `parts_qualification.md` now carry a short summary and a link instead of the pasted 48-line block. The superseded interim-board bullets of STATUS and M3_R10 moved to `docs/M3_R10.md` "Board history (superseded interim boards)" with every fact kept.
- **Owner decision table:** top of `docs/R10_VALIDATION.md` "R10 deviations for owner acceptance" (20 rows: 13 accept, 7 do).
- **Round 18 section:** `docs/R10_VALIDATION.md` "Round 18: first Claude review of committed `dcbb6c8`" (lens table with totals and report names, 36 consolidated groups each with a disposition, a "Confirmed by round 18" list, fix-pass note) and a row in the review-round log.

## Findings addressed (ID, file, what changed)

| ID | Where | What changed |
|---|---|---|
| R18-DOC-01 | M3_R10, STATUS, AGENTS, ORDERING 8, handoff, REQUIREMENTS, R10_VALIDATION top, parts_qualification | Status block stated once (M3_R10); others have a summary of at most 8 lines and a link |
| R18-DOC-02 | M3_R10, ORDERING 8, REQUIREMENTS F/P/M/ops rows, R10_VALIDATION deviations and log rows, handoff, AGENTS, STATUS | Numbers, units and words respaced; run-on records broken into sentences, bullets or tables. Historical round sections and parts_qualification outside the edited blocks left as written |
| R18-DOC-03 | AGENTS GNSS row, handoff terminals, ORDERING 8.2 table, M3_R10 Ports, REQUIREMENTS F10 | "board TXO / board RXI": the module RX goes on pin 3, its TX on pin 4 (checked against `circuit.json`: J410.3 = GPS_TX_WIRE driven by PC6 via R441); J9 stated as the reverse |
| R18-DOC-04 | AGENTS, handoff, ORDERING 8.2, M3_R10 CH1, REQUIREMENTS F8 | J121 pin 1 OUT = silkscreen E1−, pin 2 IGN = silkscreen E1+ |
| R18-DOC-05, R18-MFG-05 | M3_R10 Cost and stock, ORDERING 8.1, AGENTS, REQUIREMENTS M3, handoff, R10_VALIDATION 10 | $84.41 defined (R3's cost, parts plus feeder fees); $79.52 / $81.86; fixed fees $83.96 and handling $14.93 give about $96.32–$101.64; 17:15Z `cost_check.json` / `stock_check.json` numbers |
| R18-DOC-06 | R10_VALIDATION | Owner decision table (each row: what, why, closure, link) |
| R18-DOC-07 | ORDERING 8.1.1 | 1.733 Ah on the table's 5.546 V basis; 1.705 Ah is the nominal 5.456 V case |
| R18-DOC-08 | M3_R10 "Sources and datasheet revisions" | DS12110 cited as Rev 11; AN2606 Rev 64 (loader roles) and Rev 70 (boot patterns) explained, one URL each |
| R18-DOC-09 | AGENTS, M3_R10 CH1, REQUIREMENTS F8 | ARM1_SENSE: a name kept from R9, senses the post-load-switch bus, not an ARM link |
| R18-DOC-10 | M3_R10 Placement | Round-by-round changelog replaced by the short placement history |
| R18-DOC-11 | STATUS | IMU axis map, pin-map and terminal pointers added; nine superseded bullets moved to M3_R10 Board history |
| R18-DOC-12 | ORDERING 7 | Section marked "R9 only; for R10 use 8.4"; each stale row labelled (arming link, 15 A fuse, pull-pin, GH plug, coax, servo header) |
| R18-DOC-13 | AGENTS 1 | Table rewritten: R10 only, each cell about 600 characters or less, no repeated D-ID lists, no R168 / R170 / R172; R7 to R9 history pointed to M3_R7/8/9 |
| R18-DOC-14 | M3_R10, AGENTS, STATUS, handoff, REQUIREMENTS, R10_VALIDATION | "Two consecutive reviews (R16, R17, same reviewer family)"; round 18 is the first from a different family |
| R18-REQ-03 | REQUIREMENTS | Sources, P1, M1, Pack, Pad arming, Camera, Battery harness, accepted risks (servo containment, gate-net spacing) made R10-only; history marked |
| R18-REQ-05 | REQUIREMENTS Pack / Pad time, ORDERING 8.1.1, M3_R10 | One worksheet; no fixed Ah in REQUIREMENTS. Re-basing of the SD and logic allocations offered, not done (it would reissue sealed D-R17-01 numbers) |
| R18-REQ-06 | REQUIREMENTS P3, M3_R10 retention | 5 × 100 g kept; basis written from DESIGN_ASSURANCE 6.1 (landing 92 to 367 g, GEVS 500 g, axial deployment pull); parent VEHICLE.md has no ejection figure |
| R18-REQ-07 | AGENTS 3, REQUIREMENTS M2 | "R10 has no RF, RADIO_* or GNSS_* nets" (rules otherwise unchanged). Moving UART nets to the slow list not done: gate-scope change |
| R18-REQ-08 | REQUIREMENTS | F11 added (LEDs, buzzer, USB-C, diagnostics); temperature cold end restated; V3V3_SENSE redundancy recorded (disposition is the CAD lane's) |
| R18-REQ-09 | REQUIREMENTS F5 | The microSD is an owner-chosen convenience log (about 2 MB against 16 MB QSPI, Inference); removal list given |
| R18-REQ-10, R18-MFG-06 | REQUIREMENTS M1, ORDERING 8.2 | C84 hand-fitted after reflow and must not be in the JLC upload BOM / CPL (the instruction is valid in either state of the package) |
| R18-REQ-12 | REQUIREMENTS F6 | 0.15 s relabelled as an inherited design point; chatter test (longest drop-out below 10 ms) proposed |
| R18-MEC-01 | M3_R10 mechanics, R10_VALIDATION 8, handoff | East-edge asymmetry and the reviewer's strain numbers (Inference); tool change left to the gate follow-up |
| R18-MEC-02 | ORDERING 8.4, REQUIREMENTS P2, M3_R10, handoff, AGENTS | Nylon or insulated screws and washers at all five supports (LED2.2 3.808 mm against the 3.8 mm gate) |
| R18-MEC-03 | REQUIREMENTS P2, M3_R10, handoff | Wire room defined: to the nominal Ø 50.8 mm wall at 5 mm height, 0.5 mm allowance not subtracted (4.503 mm with it) |
| R18-MFG-01 | ORDERING 8.1 | R10 tab plan: legal windows from `check_r10` T-1 (computed read-only on `632a9ad3…`), a four-tab proposal with Gerber spans and nearest part, the OQ-4 aft-edge alternative; R9 spans marked history |
| R18-MFG-03 | ORDERING 8.1, 8.2 | VIPPO request, via sizes (291 + 4 + 1), and a three-step fallback |
| R18-MCU-01 (records) | M3_R10 Firmware, R10_VALIDATION 5 | Rule: never enable a pull-up, RTC_TAMP3 or the wakeup function on PC1 |
| R18-MCU-02, R18-PWR-02 | M3_R10 Power / Ports / Firmware, ORDERING 8.3, handoff, REQUIREMENTS F9 / F10, AGENTS, R10_VALIDATION 3, 4 | USB-only budget (0.4596 / 0.4856 A against 0.453 A; 1.61 W at the minimum limit), bench rule, park PC6 / PB13 while the ports are unpowered, "powered whenever the battery path is on" |
| R18-MCU-03 (records) | M3_R10, AGENTS, REQUIREMENTS, R10_VALIDATION 5 | PE4 active high, ODR low before output mode, GPIOE_LCKR, gate contract |
| R18-PWR-03 | parts_qualification | Removed GPS / radio switches, R410 / R420, U411 / U421, the 0.762 A bound and the GH camera-loop split marked historical; current capacitor inventory, minima, 53.13 mΩ DB125 split and the shared-port short stated |
| R18-SAF-06 | ORDERING 8.3, AGENTS, handoff, M3_R10 Firmware | Per-flight check (J121.2 below 0.1 V, pack connected, J400 open, floating meter); the firmware policy of dropping PC1 after the pad check is recorded as an owner option, not adopted |
| R18-RTE-02, -03, -05, R18-MFG-04, R18-MCU-04, R18-BOM-02 / -04 | R10_VALIDATION 6, 7, 9 and Round 18 | Per-net detour table, layer-change return numbers, USB pair, silkscreen at JLC minimum, VCAP and DB125 evidence recorded as deviations with reasons |
| R18-MEC-04, R18-REQ-04 | handoff, R10_VALIDATION | Parent VEHICLE.md stays a deviation (separately owned); the handoff terminal table is the replacement text |

## Findings not handled here (CAD / check lanes; recorded only)

R18-SAF-01 to -05, R18-GATE-01 to -09, R18-MCU-01 (R123), R18-MCU-03 (pin table, binding note), R18-PWR-01, R18-RTE-01, R18-RTE-04, R18-REQ-01, R18-REQ-02, R18-REQ-11 / R18-BOM-01 (R430), R18-BOM-03 (L400), R18-MFG-02 (U4 webs) and the parts of R18-REQ-10 / R18-MFG-06 / R18-REQ-08 /
R18-DOC-08 / R18-DOC-02 that live in CAD-owned files (`pin_table.tsv`, binding note, schematic text, BOM / CPL). They are listed in the Round 18 table of `docs/R10_VALIDATION.md` as "fixed in the round 18 fix pass (board change / check change)", written from the CAD brief.

## For the root to reconcile after the CAD pass (first-pass list; items 1 to 10 are done, see the last section)

Search for the phrases "round 18 fix pass" and "board change". Facts that depend on the final board:

1. **Board hash and metrics** (`632a9ad3…`, 2,256,162 bytes, 209 / 951 / 296 / 168, 1788.675665 mm, 118 / 91 / 40 silkscreen): `docs/M3_R10.md` "The board", AGENTS status paragraph and Manufacturing row, STATUS status paragraph, handoff status, ORDERING 8 header and 8.2 first paragraph, `docs/REQUIREMENTS.md` F7 (native allocation line), parts_qualification summary, R10_VALIDATION top and Round 18 intro.
2. **Clean pair:** every "does not carry to a changed PCB" sentence (M3_R10 Current state, REQUIREMENTS R10 acceptance, Round 18 intro, owner table rows 2 and 20) assumes a changed PCB; adjust if the board is unchanged.
3. **R123** 100 kΩ to 2 kΩ: M3_R10 "Single screw switch", CH1 text and Firmware PC1 rule; R10_VALIDATION 1(c) and 5. **Q121 second gate resistor:** AGENTS actuator row, M3_R10 Power "Pyro cell", ORDERING 8.3 coating worksheet (bottom selections).
4. **R430** to C2999509: M3_R10 Cost and stock, ORDERING 8.1 table and cost basis, AGENTS Manufacturing row, R10_VALIDATION 10 and owner row 14, group m14. The cost and stock numbers ($54.43 + $25.09 = $79.52; $81.86; 82 codes; R430 and U4 failing) come from the 17:15Z `cost_check.json` / `stock_check.json`; rerun and update them in M3_R10, ORDERING 8.1, AGENTS, STATUS, handoff, REQUIREMENTS M3 and R10_VALIDATION 10.
5. **C84 upload status:** ORDERING 8.2 "Upload status", REQUIREMENTS M1, R10_VALIDATION group m15 and the C84 row of section 9; the statements "82 BOM codes, 199 fitted parts, all included in the BOM/CPL" (ORDERING 8.2, M3_R10 board table, AGENTS) change if C84 leaves the upload files.
6. **L400 land, U4 mask webs, SD_MOSI redraw:** ORDERING 8.2 bullets (L400, U4), R10_VALIDATION groups m12, m13, m19 and the section 9 rows, M3_R10 "Retained deviations".
7. **R62 / R63 / PC3_C** if removed: REQUIREMENTS F11, the hidden-reference list in M3_R10 "Silkscreen", the coating list in ORDERING 8.3 (R62, R63), footprint counts.
8. **S-8 / ACT_GATE keep-outs:** M3_R10 CH1 sentence and R10_VALIDATION 1(a), group m01.
9. **Decision counts:** "126 D IDs through D-R17-04" in M3_R10, STATUS, R10_VALIDATION 12 and the top; add the D-R18 entries.
10. **Policy sentence:** M3_R10 "Retained deviations and Minors" says the round 18 fix pass applies Minors by supervisor decision (D-R16-03 was the policy at the R16/R17 pair); edit if that is not how the root records it.
11. **CAD-owned text still to align:** `pin_table.tsv` row 33 (ARM1_SENSE note), pin 3 (PE4 polarity), rows 51, 52, 63, 64, 78 to 81 (spacing, "R460 (10 k) to 3V3"), binding note DS12110 Rev 10 cites and the "PC6 / PB13 idle-high" obligation (needs "only while the ports are powered").

## Reconcile after the CAD pass

Second pass, done after `round18_fix_cad.md` / `.json` and `R10_DECISIONS.md` D-R18-01 … 10 were final. Same eight documents, same rules: AGENTS section 2 byte-identical (checked against `HEAD`), no tool, generator, CAD, fab or decision-record edit, no build or `check.sh`, no git state change, no local absolute paths. Board: PCB `a3144b151b58daf8ba5747def50decc4d1751ad35be478fafc89ef53aa533918`, 2,250,842 bytes; 208 footprints, 947 segments, 292 vias (166 GND), 1788.737627 mm; silkscreen 120 visible / 88 hidden / 40 legends. Cost and stock numbers are from the refreshed `cost_check.json` (23:51:50Z) and `stock_check.json` (23:50:54Z); fire and gate numbers are from `parts_budget.json` (sha256 `61727af7…`).

**Items 1 to 10 of the first-pass list**

| # | Status | Where |
|---|---|---|
| 1 hash and metrics | Done | M3_R10 "The board" (with a before to after table "What the round 18 fix pass changed"), AGENTS status paragraph and Manufacturing row, STATUS, handoff, ORDERING 8 header and 8.2, REQUIREMENTS R10 status, parts_qualification summary, R10_VALIDATION top ("Current PCB") |
| 2 clean pair | Done, wording kept | Every "does not carry to a changed PCB" sentence now names the two boards; rounds 19 and 20 are shown as planned after the gate pass (M3_R10 review table, R10_VALIDATION review-round log, owner rows 2 and 20, AGENTS, STATUS, REQUIREMENTS, handoff, ORDERING, parts_qualification) |
| 3 R123, R119, TP121 | Done | R123 2 kΩ (C4109) in M3_R10 (single switch, CH1, Power, Firmware), AGENTS actuator row, R10_VALIDATION 1 and 5, parts_qualification; R119 in M3_R10, AGENTS, ORDERING coating list; TP121 B(4,70) in the ORDERING probe table |
| 4 R430, cost, stock | Done | $79.12 (parts $54.33 incl. C84 + $24.79 feeder over 81 charged codes); no minimum-purchase uplift; $95.91 / $98.90 with fixed fees / handling; only U4 short; R430 C2999509 84,923 min 1; U9 45 min 1. M3_R10, ORDERING 8.1, AGENTS, STATUS, handoff, REQUIREMENTS M3, R10_VALIDATION 10, groups m14 / m27, owner row 14 |
| 5 C84 and counts | Done | JLC BOM 81 lines, 197 placed (66 top + 131 bottom CPL rows; 185 reconstructed + 12 placement-only), paste 245 / 371, six-output manifest, owner BOM `fab/m3_bom_owner.csv`; ORDERING 8.1 (uploads), 8.2 (package, Upload status), REQUIREMENTS M1, M3_R10, AGENTS, R10_VALIDATION m15 and section 9 |
| 6 L400, U4 webs, SD_MOSI | Done | Bourns land 2.0 × 1.8 mm at ±2.25 mm (proxy residual 0.15 to 0.05 mm); U4 webs 0.150 mm (paste 88.4 %); SD_MOSI 36.098 to 34.104 mm, 12 to 10 segments: ORDERING 8.2, R10_VALIDATION m12 / m13 / m19 and section 9, M3_R10 |
| 7 R62, R63, PC3_C | Done | REQUIREMENTS F11 rewritten (removed; VREFINT and VBAT/4); M3_R10 hidden list (88 entries), Ports, Firmware; ORDERING coating list; R10_VALIDATION m36 |
| 8 S-8, K-plane | Done | S-8 on seven barrel nets with GND foreign for ACT_GATE / ACT_DRV, all before to after gaps, nominal margin 0.050 mm; In2 3V3 one piece 1466.52 mm² (K-plane): M3_R10 CH1 / Power, R10_VALIDATION m01 / m05 and 1(a′), ORDERING rules row, handoff, parts_qualification |
| 9 decision counts | Done | 136 IDs through D-R18-10 in M3_R10, STATUS, R10_VALIDATION; the JSON ledger `r10_final_deviations.json` still indexes 126 and is said so |
| 10 policy | Done, as instructed | "The Claude supervisor applied the round 18 Minors in CAD by supervisor decision, under the owner's standing instruction to decide from flight physics and AVA without asking": M3_R10 "What the round 18 fix pass changed", R10_VALIDATION Round 18 (policy and Fix pass) |

**Residuals recorded (each measured by the CAD pass)**: PYRO1_CONT_MID 0.250 mm from R134.2 and 0.175 mm from Q123.1 behind R173 5.1 kΩ (at most 1.6 mA, no R134 or e-match bypass; the firmware check is Inference; BUZZ_G bridge at most about 4.6 V on PC14); OUT–GND approaches 0.177 / 0.180 mm unchanged; TP121's 7.14 mm ACT_GATE B.Cu stub at 0.25 mm; In2 3V3 necks about 0.50 to 0.55 mm (approximate); Q122 conducting at a 1.92 to 2.19 V gate is Inference (AO3400A RDS(on) is specified only at 2.5 V); worst-case settled P-FET |VGS| 4.74 V (was 5.19 V) and 31.9 ms to −4.5 V (was 23.6 ms), the 100 ms wait kept; ACT_EN to BAT_ENABLE 0.330 mm, NRST via 0.425 mm, GND 0.251 mm, U1.15 / U1.17 pitch 0.200 mm. They are in M3_R10 "Retained deviations and Minors", the R10_VALIDATION owner row 2 and group m03 / m04, and ORDERING 8.3 (a bench step for the gate drive). The four-stall fire current is 1.282918 A (was 1.283013 A); loop 4.617803 Ω, IGN 10.523276 mm.

**Numbers I measured myself, read-only, on copies or with no output file in the repository** (to replace first-pass carry-overs; each method was first run on `632a9ad3…` and reproduced the documented value): the 16 courtyard stroke-overlap pairs are unchanged in location and polygon gap on `a3144b15…`, and only the R400/L400 nominal model gap changes, 0.781025 to 0.820061 mm (L400's model body is 5.4 mm instead of 5.5 mm deep); `route_check --profile r10 --bumps-all`: 139 information instances (111 + 22 inside-pad + 6 leftovers, was 140 = 111 + 23 + 6), 57 off-centre entries (was 59), 45 bump windows (was 46), one new u-turn on PYRO1_CONT_MID at B(16.87,60.13), 0 failing; via sizes 287 × 0.5 / 0.3 mm, 4 × 0.6 / 0.3 mm, 1 × 1.0 / 0.5 mm (BAT_IN via at (17.5,87.3) unchanged, U401 vias unchanged); tab windows and the four best tabs identical; `fit_check --profile r10`: the same 4.536 mm and 3.808 mm support clearances; a net-level track and via comparison shows copper changes only on ACT_EN_MCU, ACT_FET_S, ACT_GATE, BAT_FAULT_N, BUZZ_G, GND (3 vias removed, 1 added), PORT_5V3, PORT_SW (L400 entries), PYRO1_CONT_MID, PYRO1_IGN, PYRO1_OUT, SD_MOSI, V3V3_SENSE (removed) and 3V3 (one via removed), so U9's BAT_IN / RAW_PROTECTED copper and the C82 / D9 loops are unchanged. The plate / strain calculation was not re-run: the documents say it was calculated on `632a9ad3…` and that it is unchanged at this precision is an Inference.

**Left for the coordinator (not filled in on purpose)**
- Rule and test counts of the final gate run: M3_R10 "Software and CAD checks" (first bullet, last sentence) and its Board history entry for `632a9ad3…` carry only what the CAD hand-back states about the check lanes.
- The gate follow-up lane (R18-GATE-02 to -09, R18-MEC-01, R18-MEC-03): R10_VALIDATION groups m18, m31 and m32 now say "Gate follow-up lane … recorded when that lane finishes"; M3_R10 (wire-room and plate-tool sentences) and the R10_VALIDATION section 8 note say the follow-up changes `fit_check` and the plate tool. Replace them with the result. Because the gate pass may also change `route_check` or `fit_check`, the read-only numbers above are marked as a run made for these records.
- `r10_final_deviations.json` still indexes 126 decision IDs and 23 mandates; D-R18-01 … 10 are not in it. `tools/test_fab_validation.py` `test_connector_mechanical_tabs_are_independently_checked` is recorded in M3_R10 as failing on both packages (not a `check.sh` suite).
- CAD-owned text (old item 11): `pin_table.tsv` and the binding note text are not touched by me; the CAD pass changed rows 3, 16 and 18 (D-R18-10). The first-pass remarks on ARM1_SENSE, the idle-high qualifier and the Rev 10 cites in those two files are still the CAD lane's.
- Rounds 19 and 20 are written as "planned after the gate pass" in every file; edit them when the rounds exist.

**Verification (documents only)**: 109 relative links (49 with anchors) resolve, including the new `#what-the-round-18-fix-pass-changed`; all 81 tables keep their column counts; `git diff --check` clean; no local absolute or temporary-directory paths; AGENTS section 2 byte-identical to `HEAD`; AGENTS table cells at most 629 characters; a sweep of the old values ($79.52, $81.86, $96.32, 82 codes, 199 parts, R430 17 < 3610, R123 100 kΩ, 5.19 V, 1.283013 A, 118 / 91, 10.5,71.5, five-output) leaves them only in explicitly historical or "was" statements. Not verified: nothing was built or run through `check.sh`; the physical, firmware and bench items are unchanged.

## Reconcile after the gate pass

Third pass, done after `round18_fix_gate.md` / `.json` (checks and the fab package only; the PCB is unchanged). Same rules: AGENTS section 2 byte-identical (to `HEAD` and to the original `dcbb6c8`), no build, no `check.sh`, no git change, no tool or decision-record edit.

- **Counts filled in** (M3_R10 "Software and CAD checks"; R10_VALIDATION "Gate lane"): check_r10 35 rules (33 plus K-power and K-lands); `check.sh` also runs the three fab content checks through `fab_manifest.py --content` and `test_fab_validation.py`; self-tests shell 10, procurement 20, fab_validation 34, fit 33, paste 16, r10_parts 5, route 67, R10 201 (5 NumPy skips under KiCad Python), NumPy HotplugNumerics and Plate 5. Marked as the implementer's numbers, to be confirmed by the supervisor's `check.sh` run on the final tree before the commit.
- **Dispositions:** R10_VALIDATION groups m18 (all nine gaps), m31 and m32 now say "Fixed in the round 18 fix pass" with the gate-lane result; m17 gains a clause (floors now pinned) and the "gaps it missed" sentence is closed. New subsection "Gate lane (round 18 fix pass, checks only)": per-gap table with the seeds that now fail, the real-board measurements, the counts, and the open Minors.
- **Open Minors recorded** (M3_R10 "Retained deviations and Minors", R10_VALIDATION "Gate lane" and section 7): SWITCH listed twice (`r10_post.py` and `WORD_LEGENDS_R10`); the RADIO legend on the J410 / J420 seam (0.000 mm from both courtyards); R150–R155 not in `STRAIN_PARTS`; no width floors for VLOGIC, PORT_5V3, CAM_5V, PORT_4V8 and 3V3 (and no real-board seed for a U9 output via without In2 fill); `r8_fab.sh` / `r9_fab.sh` fail closed on this branch (also noted in ORDERING section 1).
- **AGENTS section 5:** the command line `python3 tools/export_fab.py` became `m3_design/r10_fab.sh` (export, content checks, manifest binding); no rule changed. ORDERING 8.1 and 8.2 and REQUIREMENTS R10 acceptance now say the manifest is written only after the content checks pass.
- **Decision count:** 137 unique D IDs through D-R18-11 (M3_R10, STATUS, R10_VALIDATION). D-R18-11 is cited as the gate-pass decision; adding it to `R10_DECISIONS.md` is the CAD lane's. The JSON ledger still indexes 126.
- **STATUS:** one line for the gate pass, limited to software checks (no physical test).
- **Wording:** rounds 19 and 20 read "planned (the gate pass is done)" in every file. The M3_R10 note that `test_fab_validation.py` fails and is outside the gate was replaced: the test was rewritten and the file runs in the gate.
- **Not changed:** the plate calculation was not re-run (the strain table now lists the east-edge parts, but no new strain values are recorded); `D-R8-03` in `R10_DECISIONS.md` (the removed `R10_SKIP_FAB_MANIFEST` flag) is a decision-record edit and is left to the CAD lane.

Verification (documents only): the relative links and anchors (including `#gate-lane-round-18-fix-pass-checks-only`) resolve, all tables keep their column counts, `git diff --check` is clean, no local absolute paths; the old gate wording ("after the gate pass", "recorded when that lane finishes", `136`, `D-R18-10` as the last decision) is gone from the current text. Nothing was built or run through `check.sh`.
