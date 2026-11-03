# R10 round 24 fix pass: docs lane (2026-11-01)

Brief: `.supervisor/r24_fix_docs_brief.md`. The base is `f2b8251`.

Board read from the working tree: PCB `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f`, 2,363,951
bytes, 46 × 90 × 1.6 mm. The docs lane measured it with KiCad 10.0.7 pcbnew (read-only):

| Measure | Value on `92c3ad59…` |
|---|---|
| Footprints | 216 |
| Segments | 1057 |
| Vias | 307 (168 GND; 302 / 4 / 1) |
| Track length | 1867.046187 mm |
| BAT_ENABLE via (17.1,82.8) to BAT_FAULT_N | 0.200 mm |
| PYRO1_CONT_MID | 0.250 / 0.175 mm |
| PYRO1_OUT | 0.177 mm |
| ACT_EN | 0.330 mm |
| BAT_FAULT_N to the GND via | 0.180 mm |
| BAT_FAULT_N to the 3V3 via | 0.380 mm |
| S-8 | 12 barrels; minimum 1.021 mm |
| `R18_BARREL_KEEPOUT_*` areas | ten |
| `parts_budget.json` SHA-256 | `52ada1ed…` (only its board hash changed) |

Every other figure comes from these sources:
- `round24_fix_cad.md`;
- `round24_triage.md` / `.json`;
- `R10_DECISIONS.md` (D-R24-18 … -23, 213 IDs);
- the per-lens JSON files: 24 raw findings, namely safety 6, power 2, MCU 4, requirements 4, docs-binding 5 and gate 3.

Constraints kept:
- Docs only, and no git change.
- AGENTS §2 is byte-identical to HEAD (md5 `5549c80b…`).
- No absolute paths were added.
- Links and anchors: 0 bad (scripted check of the ten files).

## Files and statements changed

### AGENTS.md (§1 and the status paragraph)
- **Status paragraph:** board `92c3ad59…`; the round 24 results (17 real errors); the fix pass; the closing pair is now
  rounds 25 and 26.
- **Battery row:**
  - EN timing with D402 (D-R24-19): 30–130 ms; 10.3 / 8.2 / 6.3 ms; a 5.96 V pack;
  - the 18 % chatter line.
- **External-switch row:** the leakages add (TRI-02).
- **Manufacturing row:** the evidence still binds (BOM and CPL byte-identical), and M-8.
- **Plate note:** not re-run on `92c3ad59…`.

### STATUS.md
- Last-updated date set to 2026-11-01 (TRI-14).
- Status lines: the new board and rounds 25 / 26; the EN figures and the 18 % line.
- New "Round 24 review and fix pass" entry, with tests, DRC / gate, simulation and physical reported separately.
- 213 decisions.

### docs/M3_R10.md
- **Summary and board table:** hash, bytes, track length; the fab package is re-bound.
- **New table "What the round 24 fix pass changed":** D-R24-18 … -23.
  - The board-pass heading now names its boards.
- **Review table:** rows 24, 24 fix pass and 25 / 26; new closing paragraph; 213 IDs.
- **Checks:**
  - new round 24 fix pass bullet (check_r10 37 / 37, R10 263);
  - the fab bullet now separates CPL rows from orientation counts (TRI-13 pattern).
- **TRI-01:**
  - the residuals are re-measured on `92c3ad59…`;
  - enable-chain and BAT_FAULT_N text bound to the new board, with the 0.173 mm figure as `1407e850…` history.
- **TRI-02 / -03:**
  - switch network (simulation), Logic and switch, and J400 ESD;
  - rule 8's corner is 4.80 V;
  - ramp window 4.29–4.80 / 4.72–5.25 V, with the reading of out-of-window results;
  - 18 %.
- **TRI-04:** rules 4 and 5.
- **TRI-05:** ten keep-outs.
- **TRI-06:** the U401 feedback bullet is rewritten for D-R24-09.
- **TRI-09:** J2.1 3.880 mm, J2.3 3.987 mm, 0.31–0.49 mm.
- **Current statements** bound to `92c3ad59…`:
  - S-8;
  - fire budget;
  - geometric limits;
  - hot-plug;
  - routing evidence;
  - silkscreen;
  - cost (still binds);
  - open items;
  - evidence records.
- **Board history:** new `1407e850…` entry.

### docs/REQUIREMENTS.md
- F4: 5.96 V.
- F6:
  - worst cases with D402;
  - the 18 % line with the root's reason;
  - the 4.80 V PA6 corner;
  - 30–130 ms.
- F9: the leakages add; the new ramp window.
- P2: J2 figures (TRI-09).
- P3: 98–163 g (TRI-08).
- M1: the 2026-11-02 stock run, U9 28 / −83 / 7 (TRI-07).
- M2: route_check on `92c3ad59…`.
- M3 basis and status line.
- The tab-reboot bullet.

### docs/ORDERING.md
- Status. The positions, holes, vias, package, supplier snapshot, probe worksheet and closing sentence are bound to
  `92c3ad59…`.
- §8.2: 13 bottom pin legends (TRI-11).
- §8.3:
  - coating worksheet 0.200 mm on `92c3ad59…` (TRI-01);
  - C87 timing;
  - the chatter line below 18 % with its reason;
  - the ESD step: the leakages add, plus the new ramp window.
- §8.4: 98–163 g; J2 3.808–3.987 mm.
- New history row for `1407e850…`.

### docs/R10_VEHICLE_HANDOFF.md
- Status (new board, rounds 25 / 26).
- Chatter below 18 %.
- J2 figures.
- Supplier binding; plate note.

### docs/R10_VALIDATION.md
- Head, latest-review paragraph, current PCB and review-round log (rows 24, 25 and 26).
- **Round 24 board pass section:** TRI-05's Q121 wording is corrected; "EN timing figures stand" is corrected.
- **New "Round 24: ten lenses on committed `f2b8251`":** a findings index, TRI-NN → lens IDs → error → disposition,
  plus the observations.
- **New "Round 24 fix pass":** tests, DRC / gate, simulation and physical reported separately.
- **Owner preamble.**
- **Owner rows:**
  - 12 and 32: 163 g;
  - 14: binding;
  - 20: 213 IDs, 87 later;
  - 21: new figures and the 18 % pass rule;
  - 24: TRI-01;
  - 25: 4.80 V.
- **Decision rows:** D-R24-18 … -23. The ledger counts are now 213 / 87.
- **§1:**
  - inventory basis is `92c3ad59…`;
  - the Q120 gate row is marked fixed by D-R24-02 (TRI-04);
  - the BAT_FAULT_N row gives 0.200 / 0.173 mm history (TRI-01);
  - the stale "53 IDs" note corrected to 87 (it omitted D-R23 / D-R24).
- **R23-POWER-02 disposition:** now < 18 %.
- **Other sections:**
  - C87 row: new figures and the bench rule;
  - §5 QSPI: 14.102245 mm (TRI-10);
  - §6 current PCB and detour note;
  - §7 silkscreen;
  - §8 J2 (TRI-09);
  - §9 C84 paste 249 / 381 (TRI-12) and the CPL / supplier binding.

### docs/FMEA_REDUNDANCY.md
- H-6: the BAT_FAULT_N gap with its history (TRI-01).

### parts_qualification.md
- Status line.
- D402 row: the leakages add, plus the D-R24-19 figures (TRI-02).
- C87 row: new worst cases.
- Supplier binding.
- Budget bound to `92c3ad59…` (SHA `52ada1ed…`).

### AVA_LAYOUT.md
- The reading guide names "Round 24 fix pass".
- New "Round 24 fix pass" section: board identity, the three changed BAT_FAULT_N pieces, nothing else moved.

## Not done or not verified

- The plate model was not re-run on `92c3ad59…`.
- No review of `92c3ad59…` exists yet. Rounds 25 and 26 are planned.
