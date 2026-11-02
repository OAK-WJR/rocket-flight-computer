# R10 round 30: docs_binding lens

Target: commit `0afaed3`, board SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and
after (unchanged). Read-only; probes in `.supervisor/r30_docs_binding/`. JSON: `round30_docs_binding.json`.

## Totals

| Critical | Major | Minor |
|---|---|---|
| 0 | 0 | 0 |

No real error found. Every current-board statement checked in AGENTS §1, STATUS, M3_R10, ORDERING §8, the handoff,
R10_VALIDATION, FMEA, REQUIREMENTS, parts_qualification, AVA_LAYOUT, pin_table.tsv and the binding note agrees with
board `a0ec075e…`, the fab package, budget `4267634…` and binding note `c5cd0fa3…`. No link or anchor is broken.

## What was checked

- **Binding note `c5cd0fa3…`:** board, netlist, pin-table and circuit hashes match the files. All 100 `u1_pins` nets
  match U1's pads on the board. The IMU pose matches U4. Since round 28, only rule 3's obligation changed.
- **Placement:** every `Ref F/B(x,y)` in the ten current documents was compared with the 216 footprints. The only
  mismatches are dated "from → to" history or a neighbour's coordinate. Supports, outline and terminal poses match.
  Each terminal's pin nets and the legend sides in the handoff table match.
- **Board metrics:** file size, 1059 tracks, 309 vias (170 GND; 304 / 4 / 1 by size), 1866.794 mm, 123 / 93
  references and 44 legends all match.
- **Safety distances:** all recomputed with pcbnew shape distances, and all match:
  - PYRO1_OUT to GND 0.177 / 0.180 mm;
  - R173.1 to R162.1 0.794 mm;
  - PYRO1_OUT to 3V3 / 3V3A 1.050 / 1.040 mm;
  - gate nets 1.065 / 1.0585 mm;
  - RAW_ACT to GND 0.316 mm;
  - the 0.150 mm ARM1_SENSE pair;
  - EN-node pairs 0.200 / 0.330 mm;
  - CONT_MID pairs 0.175 / 0.250 / 0.415 mm;
  - BAT_FAULT_N 0.180 / 0.175 mm;
  - In2 fill edges 0.300 mm.
- **Track lengths and test points:**
  - D402 tap 4.114 mm, EN run 3.890 mm;
  - washer distances 3.808–3.987 mm;
  - probe-worksheet pad centres and test-point nets match.
- **Fab package:**
  - 81 BOM lines, 206 CPL rows (70 / 136), C535146 ×9;
  - paste 249 / 381, drill groups (308 × 0.3 mm), the two U401 VIPPO vias;
  - manifest hashes;
  - cost ($85.26, $0.85 over, $16.79, $85.80, $102.05 / $105.04) and stock (U4 9 / 2, U9 30 / −81 / 7) as recorded.
- **Budget:** 5.880831 / 4.388491 V; 1.540851 / 1.476 / 1.278747 A; 5.713 V; 0.6144 A.
- **pin_table.tsv:** the reset-contract part references and values match the board.
- **Links:** markdown links and anchors over eleven files: 0 broken.

## Fix verification (round 29)

| Item | Verdict |
|---|---|
| D-R29-01: rule 3's 47–58 µs (47.8 / 53.0 / 58.3 µs recomputed) in the binding note; only that obligation changed | confirmed |
| Binding note `c5cd0fa3…` bound and cited as current; `30796f5e…` marked as history | confirmed |
| D-R29-02: 20 required / 14 rejected phrases; test counts 268 / 72 / 34 / 33 / 16 / 5 | confirmed |
| R29-TRI-01: status lines reworded; listed figures labelled | confirmed |
| R29-TRI-03: 27 tails (27 × 1.3 mm holes) | confirmed |
| R29-TRI-04: LS120 +70 °C records and arithmetic (80–92 / 65–77 / 48 °C) | confirmed |
| Round 29 counts and decision totals (103 + 126 = 229) | confirmed |

## Observations (not counted): 6

Each is in the JSON. In short:
- R10_VALIDATION §1 (d′) is the dated round 18 record.
- Two untracked probe-artefact names appear as provenance notes.
- Two 0.2505 mm via-to-In2-fill gaps: this is the class round 27 already ruled on (the I-5 lists are not claimed
  complete).
- An unlabelled 34.853 ms in the dated 2026-10-28 audit table.
- The orientation split and the CPL side split differ but both sum to 206.
- Abbreviated relative paths.

## Coverage limits

- R10_VALIDATION and parts_qualification were checked by targeted extraction, not line by line.
- Datasheets were not re-read.
- The models were not re-run.
- No build or gate was run.
