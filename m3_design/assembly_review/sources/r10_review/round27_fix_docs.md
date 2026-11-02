# R10 round 27 fix pass: docs lane (2026-11-02)

Brief: `.supervisor/r27_fix_docs_brief.md`, plus the root's binding message after the CAD lane. The base is commit
`816038c` (board `a0ec075e…`). Inputs:
- the triage `round27_triage.md` / `.json` (R27-TRI-01 … -07 and their `all_places`);
- the CAD lane's hand-back `round27_fix_cad.md` / `.json`;
- D-R27-01 … D-R27-03 in R10_DECISIONS.

This is the final state. The first, interim version of this file was written before the CAD lane finished; its pending
items are bound below.

**Files read from the working tree at the end** (SHA-256):

| File | SHA-256 | Note |
|---|---|---|
| PCB | `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` | Unchanged; one complete build reproduced it |
| `parts_budget.json` | `ecc45417a4b9ec6ad021f52153cf2f59b547ac8e1afbd39dbd7d6e4c39f9a8bb` | Was `5204280e…` |
| `schematic.net.xml` | `535a8fdfe96c3a771a901db2bb9d2cd1a6674b001dfe1e18aa7d600e3aea7e9a` | Ports' pin functions 4V8_1 / GND_2 / TXO_3 / RXI_4, read from the file; J9 keeps 5V_OUT_1 |
| `circuit.json` | `3220e5f9d2147e757c6a50810cf2bad6f26018aa7ed0126345deb8801cb168c2` | |
| `r10_binding_note.json` | `e8f10fb3ef1c4bd8428035dc17a08accde8b69675f1449bbc30c037b6cf37a3b` | `mcu_revision` names the two Rev 11 Table 109 limits |

Budget figures read from the file:
- `pack_7V4_four_stall_loaded_V` 5.881013614959047 and `pack_6V0_four_stall_loaded_V` 4.388744837110238. The
  stall-input paragraph's 5.881 / 4.389 V match.
- `ldo_full_load_loss_W` 0.48965, which is 0.490 W.
- 70 °C junction 109.17 / 123.86 °C, which is 109.2–123.9 °C.
- 85 °C junction 124.17 / 138.86 °C, which is 124.2–138.9 °C.
- Ceiling (125 − 70) / 0.48965 = 112.32 °C/W, which is 112.3 °C/W.

GAP-3's figures round correctly from the file.

Constraints kept:
- docs only, plus one-line erratum notes in the four review records the brief lists;
- no CAD, generator, tool, decision-record or git change;
- AGENTS §2 byte-identical to HEAD (md5 of the text from "## 2." to "## 3.": `e3bdcdaa…`, both);
- no local absolute paths added;
- links and anchors: 0 bad (scripted, GitHub slugs) across the ten docs-lane files, this file, `docs/*.md` and
  README.md. The new anchors `round-27-ten-lenses-on-committed-816038c` and `round-27-fix-pass` resolve.

## Items

| Item | Files and statements changed |
|---|---|
| R27-TRI-01 | R10_VALIDATION, Round 26 observations: "(7.31 ms at 5.73 V and 7.18 ms at 5.71 V, at 70 °C; still above 7 ms; R27-TRI-01)". `round26_fix_docs.md` item 5: an erratum line ("7.18 ms is the 5.713 V figure; only 7.31 ms is at 5.73 V") |
| R27-TRI-02 (docs part) | parts_qualification, stall input: 1.56 A at 5.456 V (1.46 A plus the 0.1 A AUX allowance) and the generator's 0.6375 A logic allocation (see the note below) give 5.881 / 4.389 V (5.881014 / 4.388745 V; 5.899 / 4.414 V before; D-R27-01). GAP-3: 560 mA (460 mA plus the AUX 100 mA), 0.490 W (0.406 W before), 109.2–123.9 °C at 70 °C, 124.2–138.9 °C at 85 °C, ceiling 112.3 °C/W. Budget SHA-256 `ecc45417…`, with its history |
| R27-TRI-03 | M3_R10 Power: "1430.05 mm² on `a0ec075e…` (1466.52 mm² when D-R18-06 joined it; …)". Re-measured here with KiCad 10.0.7 pcbnew on a read-only copy: 1430.05 mm², one piece (1431.06 mm² on `92c3ad59…`) |
| R27-TRI-04 | The binding note is D-R27-02's. A sibling in the docs is fixed: R10_VALIDATION §5's "all DS12110 cites are now Rev 8" names the two Rev 11 Table 109 exceptions. M3_R10:153 is the round 19 change table, so it stays as history |
| R27-TRI-05 | FMEA I-5 (R10) and R10_VALIDATION §1: "(not an FMEA change-list item; §4.2's H-9 is the load-switch gate-source capacitor, fitted on R10 as C120)". FMEA's historical I-5 row: the clamp is marked as mislabelled H-9. `round26_triage.md` line 128: an erratum note under it |
| R27-TRI-06 | ORDERING 8.4 and the handoff: "aft of y 23.5 (y < 23.5; J440's forward body end is at y 23.45)". `round20_mechanics.md` line 11 and `round19_fix_docs.md` line 132: in-line erratum pointers to R27-TRI-06 |
| R27-TRI-07 | No current doc describes the ports' schematic, so M3:PortTerminal (pins 4V8 / GND / TXO / RXI; D-R27-03) is named only in the round 27 records: STATUS, R10_VALIDATION's index, fix pass and decision row, and M3_R10's review row and checks bullet |
| 11.5 W | No doc quotes check_r10's old power-path comment, so nothing changed |

**Note on the stall-input logic allocation (TRI-02).** The paragraph had used 0.5 A for logic. The generator's
`loaded_pack` uses `.5 + 3.3*.2/(.8*6)` = 0.6375 A, and D-R27-01's 5.881 / 4.389 V rest on it (Calculation: the same
model with 0.5 A gives 5.903 / 4.411 V). The paragraph now states 0.6375 A and its parts. Its old 5.921 / 4.436 V were
the 0.5 A, 1.46 A pair.

## Round 27 records

- **STATUS.md:**
  - status line (round 27, D-R27-01 … -03, board unchanged, rounds 28 and 29);
  - new "Round 27 review and fix pass" entry. It reports these separately:
    - software tests: R10 268 (one new), route 72, the rest unchanged;
    - DRC and the CAD gate: one build reproduced `a0ec075e…`, `tools/check.sh` exit 0, fab outputs changed only in
      their dates, supplier evidence stands;
    - simulation: hot-plug 2304 cases, 0 failures;
    - physical tests: none;
  - round 26 entry's closing line ("Round 27 then reviewed `a0ec075e…`").
  - decision count: 223 through D-R27-03.
- **R10_VALIDATION:**
  - head and Latest review;
  - review-round log: row 27 added, rows 28 / 29 planned;
  - owner paragraph and owner row 20 (223 decisions, 97 after the ledger);
  - new sections "Round 27: ten lenses on committed `816038c`" and "Round 27 fix pass", the latter with the CAD results
    and the four new hashes;
  - "Decisions after the ledger": heading and three rows D-R27-01 … -03;
  - inventory basis (97 IDs) and §12 (223 through D-R27-03).
- **M3_R10:**
  - summary, review table (27, 27 fix pass, 28 and 29) and closing paragraph;
  - decision count (two places), the open item and the evidence list;
  - a new "Round 27 fix pass" checks bullet;
  - the fab-package note (re-exported in round 27, dates only).
- **AGENTS:** status paragraph only (round 27 and D-R27-01 … -03; the closing pair is now rounds 28 and 29 on
  `a0ec075e…`).
- **Status lines:** ORDERING, the handoff, REQUIREMENTS and parts_qualification.

## Completeness sweep

`git grep -n` over docs/, STATUS.md, AGENTS.md and `m3_design/assembly_review/sources/`:

| Grep | Residual hits | Why each stays |
|---|---|---|
| `7.18 ms`, `7.31 ms`, `TCR` | `round26_safety.md` / `.json`, `round26_triage.md` / `.json` | Review records; they give both figures correctly |
| `460 mA`, `0.406`, `0.40618`, `102.49` / `102.5`, `114.679` / `114.7`, `117.494`, `129.679` / `129.68`, `135.409` / `135.41` / `135.4` | M3_R10 Power and R10_VALIDATION row "U401 thermal" | Both already "0.490 W … 0.406 W before": correct |
| (same) | R10_VALIDATION R9-PWR-01 and the round 10 section's GAP-3 row | History, labelled to their rounds |
| (same) | R10_DECISIONS (865 / 1212 / 3101 / 3103, D-R27-01's before figures); `audit_preflight.md` (dated 2026-10-28); `r10_final_deviations.json` (`632a9ad3…`); round 10–19 records | Records |
| (same) | `hotplug.md`'s 4.436898 mΩ and other digits | Coincidental |
| `5.921`, `4.436 V`, `1.46 A` (as the port load), `5.899`, `4.414` | parts_qualification's "before" figures; D-R27-01 | Labelled before figures |
| `1466.52` | M3_R10 Power (in parentheses), M3_R10's D-R18-06 history row, R10_DECISIONS | History |
| `H-9` | FMEA §4.2 (definition), FMEA's "H-8/H-9/H-10" parts row, R2_VERIFICATION ("Done (C120)") | Correct uses |
| (same) | `round22_safety.json` and `round26_triage.json` | Records outside the brief's erratum list |
| `south of y` | the two erratum'd records | — |
| `CameraTerminal`, `5V OUT`, camera pin names | R3_VALIDATION's R3 silkscreen | History; the docs name CameraTerminal only for J9 |
| `every DS12110 citation`, `all DS12110 cites`, `one DS12110 revision` | M3_R10:153 (round 19 table), R10_VALIDATION's D-R19-13 row, R10_DECISIONS | History and records |
| `5204280e`, `762bc13d`, `aeb1674f`, `b2112fb3` | `5204280e` in parts_qualification's budget-hash history only | No doc quotes the other old hashes |
| `11.5 W`, `1.56 A at 7.4` | R10_DECISIONS (D-R27-01) | Record |
| `220`, `94` (decision counts), `through D-R26-04`, `27 and 28` | 0 | — |
| `R10 267` | the round 26 entries of STATUS, M3_R10 and R10_VALIDATION | History |

## Not done or not verified

- No board, generator, check, decision-record or git change by this lane.
- The pack-sag and U401 figures are Calculations / Inferences of the budget model. This lane read them from the
  regenerated file and re-derived the pack-sag pair from the generator's formula. The CAD lane's build, check and test
  results are taken from its hand-back; root re-checked the PCB SHA-256.
- No physical test. Rounds 28 and 29 are planned on `a0ec075e…`.
