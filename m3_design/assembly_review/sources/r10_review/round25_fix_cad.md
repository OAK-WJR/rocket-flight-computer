# Round 25 fix pass: CAD lane (generated text and records; no board change)

## Scope

Brief: `.supervisor/r25_fix_brief.md`, items 1-4, on the triage report `round25_triage.md` / `.json` (R25-TRI-01, -02
and -04 in this lane). The base is `c4bb56b` (board `92c3ad59…`). Records D-R25-01 … D-R25-03 are in
`sources/r10_design/R10_DECISIONS.md` (record index 216 through D-R25-03).

Changes were made through the generators only. No board change, no git change. STATUS.md, AGENTS.md, docs/*.md,
parts_qualification.md and AVA_LAYOUT.md were not touched.

## Board

The build reproduced PCB SHA-256 `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f` exactly (unchanged), 1649 s, exit 0.

- **Counts:** footprints 216, segments 1057, vias 307 (GND 168), track 1867.046 mm, hidden designators 92 (all
  unchanged).
- **BOM, owner BOM and CPL:** byte-identical to c4bb56b. Paste 249 / 381. Supplier evidence was not re-run.

## Items

| # | Triage | Result | Before -> after | Files |
|---|---|---|---|---|
| 1 | R25-TRI-01, chatter criterion | done (D-R25-01) | See the details below the table. | `m3_design/r10_sch_check.py`, `m3_design/r10_sch.py`, `tools/test_r10_check.py`; regenerated binding note and battery_entry sheet |
| 2 | R25-TRI-02, rule 8 hold-up | done (D-R25-02) | 0.157-0.182 / 0.44-0.48 ms "from 5.3 V" -> 0.103-0.164 ms (all ports on) / 0.291-0.430 ms (shed), over VLOGIC 4.84-5.17 V (PA6 0.44-0.47 V), fraction 0.22-0.31. Calculation, re-run on the regenerated budget, whose loads are unchanged. | `m3_design/r10_sch_check.py`, `tools/test_r10_check.py`; regenerated binding note |
| 3 | R25-TRI-04, OVLO corner | done (D-R25-03) | `r10_parts.py` computes the corner with IOVLKG +/-0.1 uA (TI SLVSFC9C 6.5) at the 0.1 % divider corners: 9.97 -> 10.18 V (10.1764). Buck peak 3.645 / 3.616 -> 3.657 / 3.627 A. U9 bound 3.74380 -> 3.74386 A, still < 3.946 A, and the assert holds. Keys 9V97_* -> 10V18_*. `parts_budget.json` regenerated; `r10_parts.py --check` passes. | `m3_design/r10_parts.py`, `parts_budget.json` |
| 4 | records | done | D-R25-01 … -03 added. D-R24-19's chatter, pack-floor and open-fraction lines and D-R24-11's "EN timing figures are kept" are annotated as superseded or corrected. History is kept. | `R10_DECISIONS.md` |

Item 1 details:

- **Before:** "drop-outs shorter than … cannot trip U9", plus a bench pass of "longest drop-out < 10 ms (pack
  >= 5.96 V)".
- **After:**
  - The immunity is stated for a single drop-out, and repeated drop-outs add up.
  - The bench rule: total open time under 7 ms in every sliding 100 ms window, with U9 staying on for the whole run at
    5.73 V. Replaying the recorded waveform through the worst-corner EN model is the fallback.
  - The trip fractions (19.9 -> 5.8 % at 5.73 V; 24.3 -> 8.3 % at 6.0 V) are guidance only.
- **Figures:** the worst-corner window limits are 7.629 / 5.871 / 9.594 ms at 5.73 / 5.5 / 6.0 V. I re-ran them from the
  triage model. The adversarial-search figure (1.1173 V) is the triage's; I did not re-run it.
- **Sheet note:** it now says "a single J400 drop-out … repeated drop-outs add up".

## Checks and tests

- **Build:** `92c3ad59…` (unchanged), 1649 s, exit 0. r10_sch_check OK, DRC / unconnected / parity / ERC 0, check_r10
  37 / 37 OK (K-binding OK on the regenerated binding note), route_check 0 failing, fab content checks and manifest pass.
- **check.sh:** exit 0.
- **Hot-plug model:** 2304 cases, 0 failures (minimum -14.807 V, steepest fall 8.995 V/us, steepest rise 5.088 V/us), unchanged.
- **Tests:** shell 11, procurement OK, fab validation 34, fit 33, paste 16, R10 parts 5, route 71, R10 263 (6 numpy skips), numpy hot-plug / plate 6. All OK.
  - Updated: `test_r23_binding_note_rules_and_pin_table` (the new words required, the old ones rejected) and
    `test_r21_sheet_notes`.
- **Not run:** no physical test. The EN and hold-up figures are calculations.

## Residual grep hits

The sweep covered every tracked text file outside the docs-lane files. The phrases were `< 10 ms`, `18 %`,
`longest drop-out`, `drop-outs shorter than`, `5.96 V`, `20.0 / 24.4`, `0.157-0.182`, `0.44-0.48`, `from 5.3 V`,
`9.97 V` / `9V97`, `3.645` / `3.616` and `3.7438`. After the build:

- **Generated files:** the binding note, the battery_entry sheet and `parts_budget.json` were regenerated. They now carry 0 hits of the old phrases:
  `longest measured drop-out`, `J400 drop-outs shorter than`, `5.96 V`, `0.157–0.182`, `0.44–0.48`, `from 5.3 V`, `9V97`, `at9.97` and `18 %`.
- **History, left as history:**
  - R10_DECISIONS D-R3-01 (round 3's 9.97 V port budget);
  - D-R24-19 / D-R24-11, now annotated as superseded;
  - the D-R25 records' own "before" figures;
  - review records in `sources/r10_review/`: round13_root_fix, round14_power, round18_requirements / fix_docs,
    round19_requirements, round23_power, round24_power / requirements / safety / triage, round24_fix_cad and
    round24_fix_docs.
- **Docs lane** (off limits here): `sources/r10_design/parts_qualification.md` line 20 (5.96 V in the D402 row), line
  137 (the R92 bleed) and line 639 (the 9.97 V OVLO corner), plus every docs, STATUS and AGENTS place in the triage's
  "quoted_in" lists.
- **Numeric coincidences, not the phrase:** R9 evidence `13.645`, round 10 / 12 review numbers, R10_DECISIONS line 3156
  (a 0.157 mm track figure).
