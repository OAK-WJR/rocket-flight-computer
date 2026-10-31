# Round 19 fix pass: documentation lane (hand-back)

Scope: `STATUS.md`, `AGENTS.md` (section 1 table, single-switch scope and status paragraph, the placement pointer;
section 2 is byte-identical to HEAD), `docs/M3_R10.md`, `docs/REQUIREMENTS.md`, `docs/HISTORY.md`, `docs/ORDERING.md`,
`docs/R10_VALIDATION.md`, `docs/R10_VEHICLE_HANDOFF.md`, `docs/FMEA_REDUNDANCY.md`, `docs/M3_ACTUATOR_MERGE.md`,
`parts_qualification.md`, `AVA_LAYOUT.md` and one respacing edit in `R10_DECISIONS.md` (R19-DOC-04 only). No tool,
generator, CAD, `fab/` or review-report file was touched. No git state was changed; the staged CAD pass is untouched.

All current documents now describe PCB `50a39de5…` (46 × 90 × 1.6 mm, 215 footprints, 301 vias, 121 / 94 references,
45 legends, eight DB125 terminals), the round 19 result on `a3144b15…` (0 / 0 / 57 Minor), rounds 20 and 21 as the
next reviews, the fab package (81 JLC lines, 205 placed, paste 257 / 371), the live cost $85.35 against $84.41 (owner
decision open), stock (none short, U4 ISM6HG256X thin 9 for 5), and every D-R19-01 … D-R19-14 change including the
spare AUX port J440 and the GPS move to USART3.

## Findings (one line each)

| ID | Disposition | Where |
|---|---|---|
| R19-DOC-01 | C126 GND via (16.178,59.047) → (15.8,59.425), list marked "last verified against `50a39de5…`" | ORDERING §8.2 |
| R19-DOC-02 | Owner table: When / Blocks order? / Owner answer columns; rows 8–12 grouped; row 2 cut; "Decisions after the ledger" table (D-R18-01…11, D-R19-01…14); linked from the file head | R10_VALIDATION |
| R19-DOC-03 | New head (where R10 stands); old banners under "Historical banners", 2026-10-27 block labelled superseded | R10_VALIDATION |
| R19-DOC-04 | Live lines respaced; one-line "sealed text keeps its spacing" note at the head | R10_VALIDATION, AVA_LAYOUT, R10_DECISIONS (named D-R16/D-R17 lines), FMEA R10 banner |
| R19-DOC-05 | 0.220 → 0.218 V (3.6 V × 2 / 33) | M3_R10 Power and Firmware, FMEA I-7, REQUIREMENTS F8, R10_VALIDATION |
| R19-DOC-06 | "Seven nets" → 10 plated barrels on 6 nets; BARREL_NETS has 11 names; RAW_ACT has no barrel | M3_R10 CH1 pyro, AGENTS pyro row, R10_VALIDATION §1 |
| R19-DOC-07 | Future-tense supervisor sentence removed; past-tense statement of who ran what | M3_R10 checks and board history, STATUS, R10_VALIDATION |
| R19-DOC-08 | AGENTS points to `r10_place.tsv` and AVA_LAYOUT's reading guide; AVA_LAYOUT has a top reading guide | AGENTS, AVA_LAYOUT |
| R19-DOC-09 | "Powered-bus" / "cold" labels; "only a 5.1 kΩ path (≤ 1.65 mA)" | M3_R10 Retained deviations, R10_VALIDATION §1, FMEA banner |
| R19-MFG-01 | Board fix D-R19-06 recorded (RADIO inside J420's span) | M3_R10, R10_VALIDATION |
| R19-MFG-02 / R19-BOM-02 | CAD lane removed C84's paste (D-R19-07); manual fit applies solder locally | M3_R10 board table, ORDERING §8.2, parts_qualification, AGENTS |
| R19-MFG-03 | U4 mask text: R9-only bullet now points R10 to §8.2 (mask relief 0, 0.150 mm webs) | ORDERING §4 |
| R19-MFG-04 | Board fix D-R19-08 recorded (legends outside DB125 envelopes) | M3_R10 Silkscreen, R10_VALIDATION §7 |
| R19-MCU-01 | PA4 low = U11 IN2 = battery; port UARTs enabled only while PA4 is low, parked analog on PA4 rising or PA6 trip (SLVSEA3F Table 9-3 p18) | M3_R10 Firmware, REQUIREMENTS F9, AGENTS firmware row |
| R19-MCU-02 | DS12110 cited as Rev 8 (rev V chapter) only; rev Y cites replaced | M3_R10 Sources, Power, Firmware; AGENTS MCU row |
| R19-MCU-03 | Board/sheet fix D-R19-13 recorded | R10_VALIDATION |
| R19-MCU-04 | VREFBUF obligation (ENVR = 0, HIZ = 1; Figure 95 p286, Table 189 p291; Table 9 note 7 as Inference) | M3_R10 Firmware, AGENTS MCU row |
| R19-MCU-05 | Carried (D-R15-02, bench-qualify VCAP) | R10_VALIDATION §5 |
| R19-MEC-01 | Harness pin-identity continuity check before first power | ORDERING §8.3 / §8.4, R10_VEHICLE_HANDOFF Terminals, REQUIREMENTS F8, AGENTS pad row |
| R19-MEC-02 | C84 hand-fit heat limit (Inference, no maker profile), top preheat with bottom supported, re-inspect L1, C7, C9, R166, measure 3V3 / VLOGIC | ORDERING §8.2 |
| R19-BOM-01 | U4 ISM6HG256X fitted (D-R19-11), LSM6DSV320X consigned alternate; R18-m14 sentence corrected; FS_XL_HG 001 / 010 obligation | M3_R10, REQUIREMENTS M1, AGENTS IMU row, parts_qualification, R10_VALIDATION §10 |
| R19-BOM-03 | Temperature row lists LS120, J430, LED1, J3 with maker / supplier URLs and pages | REQUIREMENTS Temperature, parts_qualification |
| R19-BOM-04 | Carried (DB125 1.30 mm holes; R18-m11) | R10_VALIDATION §9, parts_qualification |
| R19-BOM-05 | Carried (VCAP X5R; R18-m10) | R10_VALIDATION §9 |
| R19-PWR-01 | Five feeds doubled, three not (measured reasons); pack-only power-up and C84-connected first-article checks | M3_R10 Power "Second vias", R10_VALIDATION §4, ORDERING §8.3 |
| R19-REQ-01 | Each pad-energy margin rooted or marked unrooted; re-based ~0.6 / 0.75 Ah (Inference) beside the sealed numbers; basis is an owner decision | ORDERING §8.1.1, M3_R10 Pad energy, REQUIREMENTS Pad time, R10_VALIDATION owner table |
| R19-REQ-02 | C87 220 nF (D-R19-10) with new turn-on / chatter numbers; Accepted-risks 1.1 s line replaced | REQUIREMENTS F6 and Accepted risks, M3_R10 Power, AGENTS battery row |
| R19-REQ-03 | Superseded banner (only §2.6 current); AGENTS rows point to M3_R10 Power / CH1 pyro | M3_ACTUATOR_MERGE, AGENTS |
| R19-REQ-04 | I-7: R123 2 kΩ (0.218 V) and C123 | FMEA_REDUNDANCY |
| R19-REQ-05 | F9 spaces restored ("R92 3.3 kΩ / R166 0.36 Ω", "harness R", "TP80", "both U9", "Pack change:") | REQUIREMENTS F9 |
| R19-REQ-06 | Carried; owner option (100 g × 2) written into P3 and the owner table | REQUIREMENTS P3, R10_VALIDATION |
| R19-REQ-07 | Hold-up stated as an open owner question with the numbers (0.2 ms → 100–220 µF; one 3 ms page → 470 µF not enough); no design change | REQUIREMENTS F6, M3_R10 Power, R10_VALIDATION owner table |
| R19-REQ-08 | R7–R9 M2 / M3 history and the R7–R9 acceptance sections moved verbatim; one R10 paragraph per row | REQUIREMENTS M2, M3; HISTORY §3 |
| R19-REQ-09 | Not here: parent `docs/VEHICLE.md` (root lane) | — |
| R19-REQ-10 | Not here: gate lane | — |
| R19-RTE-01 | Board fix D-R19-05 recorded | M3_R10, R10_VALIDATION §6 |
| R19-RTE-02 | TP121 removed (D-R19-03); probe tables and AVA_LAYOUT §6 row 10 updated | ORDERING §8.3, AVA_LAYOUT, R10_VALIDATION §6 |
| R19-RTE-03 | BAT_FAULT_N 0.180 / 0.380 mm neighbours recorded; §6 per-net table refreshed with the `a3144b15…` values | M3_R10 Retained deviations, R10_VALIDATION §6 |
| R19-RTE-04 | Six 0603 under-body fan-out vias (R86, R89, R91, R101, R401, R403) in the owner's M2 list | R10_VALIDATION §6, REQUIREMENTS M2, M3_R10 Routing |
| R19-RTE-05 … -08 | Carried in the M2 list | R10_VALIDATION §6 |
| R19-SAF-01 | Board fix D-R19-01; S-8 barrel table on the new board | M3_R10 CH1 pyro, R10_VALIDATION §1 |
| R19-SAF-02 | EN-node neighbours and leak thresholds; "U9 stays off" corrected; coating adds U9, R80, R81, R165, C87, BAT_ENABLE vias / tracks; per-flight switch-off check; J400 pair twisted | M3_R10, R10_VALIDATION §1, ORDERING §8.3 / §8.4, FMEA H-6, handoff, REQUIREMENTS Pad arming, AGENTS |
| R19-SAF-03 | Board fix D-R19-03 recorded | M3_R10, R10_VALIDATION |
| R19-SAF-04 | 49-row inventory (27 non-GND, min 0.173 mm) with consequences; open-match masking case | R10_VALIDATION §1, M3_R10 Retained deviations |
| R19-SAF-05 | Ring-to-foreign copper figures (J400.2 0.750, J121.1 0.803 on `a3144b15…`; ≈ 0.76 mm on the new board, Calculation) recorded as deviations | M3_R10 CH1 pyro, R10_VALIDATION §1 |
| R19-SAF-06 | AGENTS §2.4 scope stated (Q124, Q120 / Q121; Q122 now has the full network, C123) without touching §2 | REQUIREMENTS F8, AGENTS actuator row, M3_R10, FMEA I-7 |
| R19-GATE-01 … -07 | Not here: gate lane | — |

Owner-approved AUX port (D-R19-14): written into AGENTS (port row, MCU row), M3_R10 (board table, ports, firmware port
map obligation, power, mechanics), REQUIREMENTS F8 / F9 / F10 / P2, the handoff terminal table and harness text,
ORDERING §8, FMEA I-11, parts_qualification. Hidden designators C28, R110, C123, D440, D441, R88 (94): M3_R10
Silkscreen, R10_VALIDATION §7, AVA_LAYOUT.

## Places that still need the gate lane's counts

The CAD-pass numbers (check_r10 35 rules; route_check 0 failing, 22 bump windows, 7 leftovers; self-tests shell 10,
procurement 20, fab_validation 34, fit 33, paste 16, r10_parts 5, route 68, R10 212, NumPy 5) are written, labelled
"at the CAD pass", in:
- `docs/M3_R10.md` "Current state" → "Software and CAD checks" (first two bullets) and "Routing evidence" → "Current PCB";
- `STATUS.md` R10 "Round 19 fix pass" → *Software tests* and *DRC and CAD gate*;
- `docs/REQUIREMENTS.md` M2 ("0 failing on `50a39de5…` at the round 19 CAD pass");
- `docs/R10_VALIDATION.md` "Round 19 fix pass" paragraph, §6 "Current PCB `50a39de5…` (CAD pass)", §8 wire-room lines.

If the gate pass regenerates `parts_budget.json`, refresh its SHA-256 (`ca8d2f84…`) in `parts_qualification.md`.

If the owner answers the cost question or the supplier data are refreshed, the cost / stock statements are in:
M3_R10 "Cost and stock" and "Open items"; AGENTS manufacturing row and status paragraph; STATUS status; REQUIREMENTS M3,
R10 acceptance (OQ-3) and "R10 status"; R10_VEHICLE_HANDOFF "Cost"; ORDERING §8.1; the parts_qualification round 19
amendment intro; R10_VALIDATION §10 and owner-table row 14.

## Not done

- Not re-measured on the new board (stated where used): the U9 / C82 / D9 output paths, J440.2's spokes, the full
  `--bumps-all` routing inventory, the §6 per-net table, the plate model, and the surface adjacency inventory (taken
  from round 19's `a3144b15…` measurement, with the CAD lane's re-measured changes).
- Winbond W25Q128JV tPP is cited from the datasheet's AC table without a re-read page number.
- No physical, bench or firmware result is claimed anywhere.
