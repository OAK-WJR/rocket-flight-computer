# R8 build and validation

**Build steps 0–9 of `r8_plan.md` are done (the step table below states each step's verification as run, with the misses
and relaxed checks named). Review pass 1 ran on the step-9 board `429b6db4…` (0 Critical, 1 Major, 38 Minor) and fix pass 1
implemented it; review pass 2 ran on fix pass 1's board `6600ef94…` (0 Critical, 0 Major, 31 Minor), review pass 3 on
fix pass 2's `990c8040…` (0 Critical, 0 Major, 26 Minor) and review pass 4 on fix pass 3's `c84f00b8…` (0 Critical,
0 Major, 16 Minor). Fix passes 2, 3 and 4 implemented the Minors marked worth fixing, all through the generators, tables
and tools. The final board is `cc044ea0…` (fix pass 4: pass 4's two copper Minors, each the pass-4 routing reviewer's own
trialled variant, D110 / D111, and four record items). Passes 2, 3 and 4 found no Critical or Major; review pass 5, a
focused confirming pass in three of the eight dimensions (build integrity, planes and return paths, routing), re-checked
fix pass 4's board `cc044ea0…`: 0 Critical, 0 Major, 3 Minor (two record items and the owner's commit; its records pass
changed records only, so the board is still `cc044ea0…`); on 2026-10-20 the owner accepted the R8 deviation list (below), including the C10 vibration item and the listed agent decisions;
still open: U4 consigned, JLC's tab acceptance and a cost and stock run within 24 h.**
Every qualification a re-placement invalidates was re-measured in step 9, and each fix pass re-measured what its changes
touch (below). The owner's dated acceptance of the R8 deviation list (REQUIREMENTS M2) is not recorded. No fabrication
or flight release is approved by this record. R7 (`c872a3d3…`, owner-accepted 2026-10-18) stays the orderable fallback.
Design record: [M3_R8.md](M3_R8.md); decisions: `m3_design/assembly_review/sources/r8_design/R8_DECISIONS.md`
(D1–D111); step handoffs: `sources/r8_design/r8_step*_handoff.md`; reviews: `sources/r8_review/pass1_*.md`,
`pass2_*.md`, `pass3_*.md`, `pass4_*.md`, `pass5_*.md` (integrity, planes, routing); fix passes:
`sources/r8_review/fix1_handoff.md`, `fix2_handoff.md`, `fix3_handoff.md`, `fix4_handoff.md` (the records passes after
review passes 4 and 5 have no handoff: "Review pass 4" and "Review pass 5" below list what each changed).

## Baseline and build summary

- **Baseline:** R7, commit 431025d, board SHA-256 `c872a3d30509cccf5f78b64cde48ef722ee85c7be23c4848b07ce4082a852de3`
  (owner-accepted). Branch `m3-assy-r8`, uncommitted.
- **Plan:** Strategy B (r8_plan section 1): partial re-placement with planned-bus routing; rigid, hash-asserted R7 copper
  for the RF strip, the CH1 block, PYRO_BLOCK, J1, J122 and its tie holes, the M3 holes and the outline.
- **Final board (fix pass 4):** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  **`cc044ea0922ff826df19af9d9726d92c096ab2b127025b55d123d8772e5fb4a7`**; netlist `0cc1ed692fb99dd2…` (unchanged); fab
  manifest bound to it (5 outputs). Reviewed boards: `429b6db4dc95c1a0fd3e736625c416c20fa0e7fc72f6f6c9c576003340dc1987`
  (step 9, review pass 1), `6600ef9462b37ec58540e0dd7edd97577c3e778bda0d233d3c1dffc555ad5a8d` (fix pass 1, review
  pass 2), `990c8040c5b8457bd2bd1717ed3e5c2725f32c1dda1cd7f826a0c2b458d28b18` (fix pass 2, review pass 3) and
  `c84f00b88f5fb9409de40f33b2d51a48fb29fb66c386c869b7f93ea791e37c54` (fix pass 3, review pass 4).
- **Reproducible:** `m3_design/r8_build.sh` rebuilds sheets, netlist and board byte for byte from 431025d (about 10 min;
  two consecutive builds in fix pass 4 gave `cc044ea0…`, all 15 sheets, the netlist and the board identical);
  `m3_design/r8_fab.sh` makes and checks the fab package.
- **Generator state:** uncommitted in the worktree (no commit on `m3-assy-r8`; AGENTS: the owner asks for commits, and
  no fix-pass or records-pass brief allowed one), so no commit hash can stand beside the board SHA. No reviewed state was
  preserved as a commit: pass 1's (`429b6db4…`) was overwritten by fix pass 1 (its deltas: `fix1_handoff.md`), and pass
  2's (`6600ef94…`) by fix pass 2, which recorded the SHA-256 of every changed or untracked file before it started
  (`sources/r8_review/fix2_baseline_sha256.txt`, 222 files) and lists every file it changed in `fix2_handoff.md`.
  Pass 3's state (`990c8040…`) was not committed either (R8P3-INTEGRITY-04); the review coordinator kept a backup of it,
  and fix pass 3 recorded the SHA-256 of the files it started from (`sources/r8_review/fix3_baseline_sha256.txt`) and the
  diff of its code and table files (`fix3_generators.diff`). Review pass 4 reviewed `c84f00b8…` in this uncommitted
  worktree; its records pass changed records, `step9/requalify.py` and one evidence file only, so the board and every build
  output are still `c84f00b8…`'s (R8P4-INTEGRITY-01: the reviewed state now survives only here and, for `990c8040…`, in the
  session scratchpad backup). Fix pass 4 started from that state: it recorded the SHA-256 of every changed or untracked
  file first (`sources/r8_review/fix4_baseline_sha256.txt`, 276 files; the coordinator also kept a backup of the
  `c84f00b8…` state in the session scratchpad) and the diff of its code and table files (`fix4_generators.diff`), and it
  did not commit either. Review pass 5 reviewed `cc044ea0…` in this uncommitted worktree (R8P5-INTEGRITY-01): it rebuilt
  the `c84f00b8…` state from 431025d and that backup (all 276 baseline hashes verify) and found fix pass 4's changed
  files exactly the handoff's list; its records pass changed records only, so the board and every build output are still
  `cc044ea0…`'s, which exists only in this worktree. Owner action (R8P1–R8P5-INTEGRITY): commit or tag this state on
  `m3-assy-r8` (`git add -A`; nothing R8 needs is gitignored) and record the commit beside `cc044ea0…` here and in
  STATUS; later fix passes diff against it.

| Step | What it produced | Board after it | Verification (as run; misses and relaxed checks named) |
|---|---|---|---|
| 0 Decisions, datasheets | D1–D14, `pin_table.tsv` (100 pins, every row cited) | R7 | every row cited; fallbacks agreed; table reproduced byte for byte |
| 1 Gate tools | `check_r8`, route_check profiles (allowlist A8 only), `dc_solve --necks`, `ipc2152.py`, scorecard tools | R7 | each new check fires on a seeded defect (test_r8_check 20, test_route_check 57); the plan's independent tool review was not done in step 1 (no reviewer available, `r8_step1_handoff.md`): done by R8 review pass 1 (build integrity, 0 Critical / 0 Major) |
| 2 Schematic | `r8_sch.py`: 27 U1 pins, R310.1 to 3V3 | R7 | ERC 0; netlist diff = exactly the 28 decided changes; parity; no RF pin on a safety net |
| 3 Spikes (a)–(d) | under-U1, servo / D121, battery band, RF buses (session scratchpad; their copper became step 4's reservations) | — | DRC 0, route_check 0 on spike nets; no kill rule fired (flash under U1, D121 kept, the band as spike c) |
| 4 Placement | `r8_place.tsv`, `r8_pcb.py`, `r8_legalise.py`, D29–D39 | `40e516fa…` | 11 gates: rigid, legaliser, DRC + parity, F10, fit ≥ R7, tabs, MST 1632 mm, contract, actuators |
| 5 Power | `r8_power.py`, D40–D50 | `1818b05f…` | DRC with pyro rules A–H, D18 / D19, In2 map, 7.7 A necks within D12 |
| 6 Signals | nine family modules, D51–D61 | `b7a4d34d…` | per family: connectivity, DRC, route_check, budgets |
| 7 Ground | `r8_ground.py` / `.tsv`, D62–D67 | `52c643d6…` | 14 gates pass; the plan's step-7 targets do not: C6 = 1 (A8), P7 = 1, P9 / P10 missed (4.48 / 9.65 mm against 3.5 / 7 mm), dispositioned by D68 for the owner's acceptance (C2, C3) |
| 8 Post and fab | `r8_post.py`, `r8_fab.sh`, `paste_check.py`, D68–D73 | **`429b6db4…`** | `tools/check.sh` exit 0 in every build; byte-identical rebuilds; cost $106.00 with 52 extended codes |
| 9 Requalify, records | measurements below, `tools/reference_audit.py`, binding note, records, D74–D84 | `429b6db4…` (unchanged) | every invalidated item closed with evidence or listed as a bench item; `tools/check.sh` exit 0 |
| Fix pass 1 | review pass 1's findings in the generators, tables and tools (D85–D96), the M2 sweep script, records | `6600ef94…` | two byte-identical builds; `tools/check.sh` exit 0 (with the new `check_r8` gates); the DC neck gate in the build; 272 tests in 17 suites; fab package regenerated and checked |
| Fix pass 2 | review pass 2's Minors marked worth fixing (D97–D105): the In2 BAT_IN trim, four 0.5 mm vias, R81 off the BAT_IN feed, C83.2's link, J123.2's relief, the IC GND-pad via stage, battery_pyro's drain, the M2 sweep's pad adjacency, records | `990c8040…` | two byte-identical builds; `tools/check.sh` exit 0; the DC neck gate in the build; `make_ground.py --built` reproduces `r8_ground.tsv`; 272 tests in 17 suites; fab package regenerated and checked; the M2 sweep, DC solves, reference audit, requalify, pyro neighbours and scorecard re-run on `990c8040…` (evidence `step9/evidence/fix2_*`) |
| Fix pass 3 | review pass 3's findings (D106–D109): USB_LIMITED's trunk and R172 0.05 mm off their neighbours, CAM_PWR_EN's lower leg as one 45° run, R165's BAT_ENABLE via as a signal via, the sweep's margin-free search, records and bench steps | `c84f00b8…` | two byte-identical builds; `tools/check.sh` exit 0; the DC neck gate in the build; every step gate (the camera budget tightened to 1.40, L10's R172 figure re-measured); `make_ground.py --built` reproduces the regenerated `r8_ground.tsv`; 272 tests in 17 suites after the fab step; fab package regenerated and checked; the M2 sweep, DC solves, reference audit, requalify, pyro neighbours, scorecard and binding note re-run on `c84f00b8…` (evidence `step9/evidence/fix3_*`) |
| Pass-4 records pass | review pass 4's record, procedure and tool corrections (no D-number: no design decision): ORDERING §5's bootloader pyro-gate step, coexistence spectrum checks and stall-test lines, records, `requalify.py` rule G | `c84f00b8…` (unchanged) | `tools/check.sh` exit 0; board, netlist, sheets, ground table and fab outputs byte-identical to before the pass (SHA-256 of each checked); `requalify.py` re-run on `c84f00b8…` (rule G added to `fix3_requalify_r8.json`, every other key equal) |
| Fix pass 4 | review pass 4's two copper Minors (D110, D111): the radio trio centred in its fence opening with three GND vias 0.05 mm west, R87.1's branch as a T off the USB_LIMITED trunk; four record items (ORDERING's camera-supply distances, the thermal-relief rule as built, R70's fix-pass-3 designator move, `r8_build.sh`'s trim count) | **`cc044ea0…`** | two byte-identical builds; `tools/check.sh` exit 0; the DC neck gate in the build; every step gate (the rf family 436.9 of 445 mm); `make_ground.py --built` reproduces the regenerated `r8_ground.tsv`; 272 tests in 17 suites after the fab step; fab package regenerated and checked (BOM and CPL unchanged); the M2 sweep, DC solves, supply paths, reference audit, requalify, pyro neighbours, scorecard and binding note re-run on `cc044ea0…` (evidence `step9/evidence/fix4_*`) |
| Pass-5 records pass | review pass 5's record corrections (no D-number: no design decision): the scorecard intro's R-row statement (R8P5-PLANES-01, also in `fix4_handoff.md`), the In2 3V3 antipad in fix pass 4's notes (R8P5-INTEGRITY-02), the commit paragraph's wording, the review status here and in M3_R8, STATUS, README and ORDERING | `cc044ea0…` (unchanged) | `tools/check.sh` exit 0; board, netlist, sheets, ground table and fab outputs byte-identical to before the pass (SHA-256 of every file outside the edited records checked) |

## Hard gates (r8_plan section 2), on `cc044ea0…`

| Gate | Result |
|---|---|
| `tools/check.sh` 0 | **exit 0** (fix pass 4, in both builds and standalone; again in review pass 5 and after its records pass): DRC 0 at every severity, unconnected 0, parity 0, ERC 0; metadata / 3D audit OK; silkscreen in the outline; check_r8 OK; route_check r8 OK; check_actuators OK; fit_check OK |
| check_r8 | OK: 12/12 rigid digests equal R7's; U1 map 100/100; pulls (R310 on 3V3, MCU end); loader pins per D5; F10 5 mm (nearest 5.94 mm part, 5.08 mm fast line); D18 2.65 mm; D19 none; S15 / S16 (only D70's rigid link); fence (openings ≤ 2.7 mm); strip GND reach; and since fix pass 1 battery_pyro (BAT_IN / ACT_FET_S ≥ 1.0 mm from bus, igniter and, since fix pass 2, drain copper: nearest 1.089 mm, ACT_FET_S to J124.1; the drain's nearest 3.562 mm, R82.1 to J121.1; D85, D103), via_paste (709 pairs; no via ring overlapping an aperture, 0 mm, and no hole within 0.1 mm of one, nearest ring 0.025 mm from C90.1's paste, D87: looser than R7's r7_route.ViaCheck, which keeps the whole ring 0.1 mm clear; by that rule 12 via–aperture pairs at 11 vias since fix pass 3 drew R165's via at 0.5 mm (D108; fix pass 2 13 at 12, fix pass 1 14, R7 5), every one own-net and tented, the worst 0.025 mm as R7's worst (R8P3-DFM-02: kept as it is, a lost sub-0.10 mm mask web wets a same-net ring and cannot short) and terminal_legends (10 legends, each nearest its own pin, D92) |
| check_actuators unchanged | byte-identical to R7's (SHA-256 asserted by check_r8) and OK |
| Fit margins ≥ R7's | every category ≥ R7 (M3_R8 "Mechanical"; C84 1.37 mm against 0.11 mm) |
| Byte-identical rebuilds | fix pass 4: two consecutive builds `cc044ea0…`, every sheet, the netlist and the board identical (fix pass 3: `c84f00b8…` twice; fix pass 2: `990c8040…` twice; fix pass 1: `6600ef94…` twice; step 8: `429b6db4…` twice; step 9 reproduced it) |
| route_check C1 / C3 / C4 / C6 = 0 except owner-accepted inherent items | **met: the owner accepted A1–A3 on 2026-10-20** with the R8 deviation list (two, D51 and re-measured D87, are new to R8's list); C1 = C3 = 3 (A8 and the two limiter detours, D11's agreed fallback); C4 = 0; C6 = 1 (A8) |
| F10 separation counting R306 / R313 / R315 as RF parts | met: R306–U1 5.94 mm, R310 / R313 / R315–U1 6.04 mm |
| No inner RAW_ACT / BAT_IN within 2.5 mm of PYRO1_BUS / IGN / OUT | met: nearest 2.65 mm (BAT_IN In2 to R134.1) |
| PYRO1_GATE_N ≥ 0.5 mm from servo PWM | met: none under 0.5 mm on any layer pair |
| Reset / loader pin table: only LEDs on loader-driven pins | D5's rule met (LEDs plus seven reasoned pin-net pairs: PA2 SERVO3_MCU, PA11 / PA12 USB_DM / USB_DP, PB6 QSPI_NCS, PB9 I2C1_SDA, PB10 RADIO_SCK_MCU, PB14 RADIO_MOSI_MCU; `check_r8.LOADER_ALLOWED`); the plan's LEDs-only rule is not (D5 relaxes it: an agent decision taken on the owner's behalf, for the owner to accept with the list) |
| S15 = S16 = 0 | S16 = 0; S15 = 3.4 mm, the rigid CH1 link, D70's named exception (D70 relaxes the plan's S15 = 0: an agent decision for the owner to accept with the list) |

## Scorecard (`tools/run_survey.sh`, against r8_plan section 2)

Fix pass 4's run on `cc044ea0…` (`NO_GATE=1 NO_DC=1 tools/run_survey.sh`, with the 0.05 mm DC solves of `tools/run_dc.sh`
added to the survey folder for the D rows; the gate ran separately; `step9/evidence/fix4_scorecard.md`): simplicity
index **15.3** (R7 = 100, target ≤ 35; fix passes 1–3 15.3, step 8's full run 16.0; the quick index without the DC rows
is 13.7, as in fix passes 1–3). Targets: 20 met, 11 missed (as in fix passes 1–3). Fix pass 3's value is given in
parentheses where fix pass 4 changed a row (S1: D110's three radio lanes, +0.3 mm in all; S6, S7: those and D111's
1.86 mm shorter R87.1 branch; C2: D111's T); no P or D row moved, and of the R rows only R7's sample count (+24 on
RADIO_MISO_MCU's longer lane, none unreferenced; R8P5-PLANES-01). D110 moved three GND vias 0.05 mm: In1 / In2 fills and
the GND-via distances are unchanged at the scorecard's resolution (the In2 3V3 antipad round the stitch via moved with it,
area unchanged, R8P5-INTEGRITY-02); the three 0.05 mm solves are identical to fix pass 3's, line for line. Review pass 5
reproduced this scorecard row for row on `cc044ea0…`.

| Metric | R7 | R8 (fix pass 4) | Target | Met |
|---|---:|---:|---|---|
| S1 signal track | 3355 mm | 1497.9 mm (1497.6) | ≤ 2300 | yes |
| S4 signal layer-change vias | 217 | 55 | ≤ 75 | yes |
| S6 / S7 detour | 1.396 / 1081 mm | 1.174 / 285.8 mm (1.175 / 287.4) | ≤ 1.18 / ≤ 350 | yes |
| S8 / S9 nets over 1.6× / 2× | 23 / 12 | 4 / 4 | 0 except keep-out-forced | no (C5: RAW_ACT_SENSE_MCU, RADIO_TXEN, and the limiter's GNSS_LNA_EN 2.06 / GNSS_VCC_RF 2.37 since their vias left the paste, D87) |
| S10b bends | 648 | 231 | ≤ 400 | yes |
| S12 critical layer changes | 73 | 25 (0 without a GND via) | ≤ 32 | yes |
| S15 / S16 inner track | 901 / 0 mm | 3.4 / 0 mm | 0 / 0 | S15 no (C1, D70) |
| S17 placement MST | 2727 mm | 1638.9 mm | ≤ 1850 | yes |
| C1 / C3 gated / allowlisted | 74 / 45 | 3 / 3 | ≤ 1 (A8) | no (A2, A3: D51, D87) |
| C2 information | 252 | 91 (90) | ≤ 80 | no (C19 gives each category's measured reason) |
| C4 / C5 / C6 | 29 / 0 / 9 | 0 / 0 / 1 | 0 / 0 / ≤ 1 | yes |
| P1 In1 GND coverage | 0.880 | 0.9051 | ≥ 0.90 | yes |
| P3b / P4 | 16 / 8 | 4 / 5 | ≤ 4 / ≤ 5 | yes (the four In1 "slots": the SPI1 / IMU_CS via cluster beside U4's aft pad row, x 8.29–11.00, y 55.15–56.85, which SPI1_SCK's F.Cu edge passes (34 samples, inside the reference audit's 226 "other via" samples, C6); the thermal-relief rings round J3's legs 1 and 4, D89; and since fix pass 2 J123.1's antipad merged with J123.2's relief ring, D101; no critical track crosses the last three; R8P3-PLANES-02) |
| P6 In2 perimeter | 1581 mm | 1752.2 mm | ≤ 900 | no (C4) |
| P7 outer GND islands ≤ 1 via | 32 | 1 | 0 | no (C2, D68) |
| P9 / P10 GND-via distance | 6.12 / 13.78 mm | 4.47 / 9.65 mm | ≤ 3.5 / ≤ 7 | no (C3, D68) |
| R1 / R3 unreferenced (length) | 60.3 / 115.9 mm | 2.9 / 2.9 mm | ≤ 5 / ≤ 15 | yes |
| R6b critical-reference share | 0.279 | 0.1107 | ≤ 0.08 | no (C6, D74) |
| 7.7 A neck rise RAW / BAT / FET | 38.3 / 30.2 / 44.2 °C | 17.5 / 14.5 / 21.4 °C (dc_solve; the scorecard's own rounding gives 21.5) | ≤ 20 / 20 / 30 (D12) | yes |

Other rows that moved in fix pass 4: S2 total track 2088.8 → 2087.2 mm, S18 segments 795 → 794, R7 extended
reference samples 102,384 → 102,408 (the longer trio lanes; unreferenced samples unchanged, 5,944). Every other row
equals fix pass 3's (fix pass 3 had moved S1 1499.6 → 1497.6 mm, S2 2090.8 → 2088.8 mm, S6 / S7 1.177 / 289.4 → 1.175 /
287.4, S10 1.540 → 1.542, P1 0.905 → 0.9051, P6 1752.5 → 1752.2 mm; fix pass 2 S2 2090.0 → 2090.8 mm, S18 794 → 795,
P3 15 → 16, P8 8.12 → 8.15 vias/cm², D_bat 0.42 → 0.45 mΩ against fix pass 1).

## Requalification: what a re-placement invalidates (survey_constraints section 13)

Each item measured on `429b6db4…` in step 9 (scripts `sources/r8_design/step9/`, commands in `r8_step9_handoff.md`).
Fix pass 1 re-measured on `6600ef94…` every item its changes touch (evidence `step9/evidence/fix1_*`): the DC solves, the
pyro neighbours and rule margins, the reference audit, the tab windows, the fab package, the binding note; the rest is
unchanged by construction (the rigid copy, placement but for C83, the mechanical inputs but for one 0603). Fix pass 2
re-measured the same set on `990c8040…` (evidence `step9/evidence/fix2_*`, each bound to the board's SHA-256; before it
changed anything it re-ran fix pass 1's four unbound evidence files on `6600ef94…`, found them identical and added the
board's SHA-256 to them, R8P2-INTEGRITY-05); its placement change is R81 (an 0603, D100), and its other copper changes
are an inner-layer trim, four via rings, one GND via, one stub and one thermal relief. Fix pass 3 re-measured the same set
on `c84f00b8…` (evidence `step9/evidence/fix3_*`, each bound to the board's SHA-256): its placement change is R172 (an
0402, 0.05 mm, D106; "an 0603" until review pass 4, R8P4-DFM-01), and its copper changes are USB_LIMITED's trunk (0.05 mm), CAM_PWR_EN's lower leg, one via ring
(D108) and one regenerated step-7 cover via. Fix pass 4 re-measured the same set on `cc044ea0…` (evidence
`step9/evidence/fix4_*`): it moved no part; its copper changes are three radio lanes below the strip fence, three GND
vias 0.05 mm (two fence vias and the MISO–MOSI stitch via, D110) and USB_LIMITED's R87.1 branch (D111); no 7.7 A copper.

| Item | Status | Evidence (M3_R8 section) |
|---|---|---|
| F4 DC solve of the 7.7 A copper | **Closed** (fix pass 4 re-run) | 0.05 mm on `cc044ea0…`, every output line equal to fix pass 3's (and fix pass 2's): RAW_ACT 1.45, BAT_IN 0.45 (fix pass 1 0.42, D97), ACT_FET_S 0.18 mΩ; per-via maxima 0.86 A (RAW_ACT) and 0.65 A (BAT_IN); the servo GND return 0.69 mΩ (5.3 mV and 0.041 W at 7.7 A), equal ("DC solve"); supply paths at 0.1 mm, every row re-solved: all equal to fix pass 3's but USB_LIMITED 52.62 → 52.66 mΩ (D111; fix pass 3 52.61 → 52.62, D106) (same section); the build gates the necks at 0.1 mm (D95) |
| IPC-2152 necks and R7's C1 acceptance | **Closed** | necks 5.94 / 6.99 / 4.97 mm, 17.5 / 14.5 / 21.4 °C (0.05 mm, `cc044ea0…`, as on `c84f00b8…` and `990c8040…`), all within D12; R7's C1 deviation does not carry to R8; MARGIN P1-9's 10 mm is still not met as written (MARGIN_PRESCRIPTION) |
| Critical-reference sampling | **Closed**, R6b a measured miss (11.07 %, fix passes 2–4 equal to fix pass 1, sample for sample but the board path; the extended set 5.81 → 5.80 % in fix pass 4: 24 more samples on RADIO_MISO_MCU's longer lane, none unreferenced) | `tools/reference_audit.py`: every unreferenced sample at a via antipad or under the crystal keep-out; none over another fill, a split or a void (D74) |
| Vibration estimate | **Closed** (estimate); tap check on the bench | f1 209–490 Hz with the plugs on the sled, 6–8 % below R7 (C84), D75; fix pass 1 moved only C83, fix pass 2 only R81 (0603s) and fix pass 3 only R172 (0402, 0.05 mm); re-run by R8 pass 2 DFM on `6600ef94…` (69 of 69 values equal), pass 3 DFM on `990c8040…` and pass 4 DFM on `c84f00b8…`: every value equal to `plate_r8.json` but the board SHA (the model carries every part as a model-box-volume mass; R172's is about 0.5 mg; R8P4-DFM-01) |
| Tab windows, order mark, ORDERING coordinates | **Closed** | ORDERING regenerated (D81); fix pass 1 moved the left forward tab to y 112.5–117.5 (D93) and re-measured the table on `6600ef94…`; fix pass 2: windows, tabs and order mark unchanged on `990c8040…` (`requalify.py`), the right forward tab now GND on all four layers (D97); fix pass 3: `requalify.py` equal on `c84f00b8…` (one exit's nearest-net coordinate moved with USB_LIMITED); the left middle tab's In2 3V3 recorded in ORDERING §3 (R8P3-POWER-05); fix pass 4: `requalify.py` equal on `cc044ea0…` (every section, rule G included, but the board SHA) |
| Deviation list | **Re-made** for R8 (below), completed in fix pass 1 (C11–C18, part F), fix pass 2 (pad adjacency in C12, C19) and fix pass 3 (C20; the margin-free search in part F), corrected after review pass 4 (C12 #5 / #6, C12b #3, C4; C21 added) and in fix pass 4 (C12 #5 / #6 and C21 removed, D110 / D111; C12 renumbered; C19 / E 91); acceptance open | bound to `cc044ea0…` (`step9/evidence/fix4_m2_sweep.json`) |
| Pyro block coating and leakage distances | **Closed** | rigid block, re-measured: bare gate to bare bus / igniter 1.03–2.00 mm (= R7); no bare 3V3 / RAW_ACT within 5 mm of a pyro gate pad |
| Pyro exits and rule margins | **Closed** | every rule's closest approach listed; exits on B.Cu without In2 hops; 7 non-pyro nets within 3 mm of armed copper (R7: 23); fix pass 1: ACT_FET_S 1.089 mm from J124.1, RAW_ACT 1.115 mm from R127.1 (D85), BAT_ENABLE's crossing recorded (pyro observations below); fix pass 2: rule margins equal (`requalify.py`), 40 GND vias in PYRO_BLOCK (nearest armed-live 0.522 mm, J121.2), the drain's GND neighbours and R81's move recorded (pyro observations); fix pass 3: `pyro_neighbours.py` and the rule margins equal to fix pass 2's; R81.2 and the actuator-gate pour figures added (pyro observations, D109); after review pass 4: rule G (gate nets in the block, 0.3 mm) added to `requalify.py`, which had covered 8 of the DRU's 9 pyro rules: 0.300 mm, margin 0, GATE_N lane x 18.75 to the CONT lane x 19.25 on B.Cu (R7 0.316 mm), M3_R8's table (R8P4-PYRO-01); fix pass 4: `pyro_neighbours.py` and every rule margin equal on `cc044ea0…` (its copper edits lie outside PYRO_BLOCK and 3 mm of armed copper) |
| A8 re-measure | **Closed** | TP122's via: hole 0.60 mm inside the pad, nearest GND via 2.717 mm, nearest foreign copper 1.001 mm; the allowlist reason holds |
| F9 reverse hot-plug premise | **Closed** (model); bench test stays | protection parts within 3.9–10.6 mm of J1.1 (J1.1's centre to each part's nearest pad centre, R167 3.86 mm; pad edge to pad edge 1.9–7.8 mm, J1.1's pad square, R8P3-POWER-04); U9's feed adds ≤ 0.002 V / 0.8 % slew (D76, Inference) |
| IMU axis map | **Closed**: unchanged; bench sign check stays | bottom, rotation 0, pad 1 as R5; lever arm x −13.0 mm, sign flipped (D77) |
| Firmware board binding | **Note recorded**; binding open (no firmware) | `step9/r8_binding_note.json` (D78), regenerated on `cc044ea0…` (fix pass 4; the pin map and constraints unchanged) with constraint D6.8 (before a bootloader jump, in order: PE4 low; the SX1262 asleep and PE9 low; GPIOE reset last; PE4 since fix pass 2, R8P2-PYRO-03, the order since fix pass 3, R8P3-RF-01); ORDERING §5 checks it on the bench (R8P3-REQUIREMENTS-01) |
| RF measurement tables | **Closed** | strip rigid (field solve, launch, stitching carry over); separations, interface lines and fast-line distances re-measured |
| fit_check figures in documents | **Closed** | REQUIREMENTS, ORDERING, M3_R8 updated |
| Fab package, CPL corrections | **Closed** (fix pass 4 re-run) | manifest bound to `cc044ea0…`; BOM `be711876…` byte-identical; CPL `ef90bfa1…` unchanged by fix pass 4 (no part moved; fix pass 3 changed only R172's row from fix pass 2's `25cfed69…`, which changed only R81's from fix pass 1's `c0ee08ae…`); fix pass 4 changed the copper and drill Gerbers only (silkscreen 571 of 571 items equal); fix pass 3's rebuild had also re-placed R70's designator by (+0.104, −0.173) mm through `r8_post.py`, bottom silkscreen only, still nearer its own part (R8P4-DFM-02); CHECK none; CPL verify 85 + 126 rows, worst 0.491 mm; paste check OK |
| Cost and code count (M3) | **Closed** (step 8), binding to refresh | $106.00 per board, 52 extended codes (BOM unchanged); `cost_check.json` still names the step-9 CPL (`d26572d3…`): refresh with `FAB_NET=1 m3_design/r8_fab.sh` within 24 h of ordering |
| Circuit analyses touched by layout | **Closed** | F7: RAW_ACT Q121 → J124.2 0.44 mΩ (R7 1.50); Q30's limiter copper equal to R7's (0.2 mm B.Cu), so M3_R7's +30–40 K note holds |
| REQUIREMENTS / VEHICLE text with R7 coordinates | **Closed** / proposed | REQUIREMENTS updated; parent VEHICLE row proposed in the step-9 handoff (D84) |
| Review history | **Met for the review count**; the final board re-checked in three dimensions | review pass 1 (0 Critical, 1 Major, 38 Minor), review pass 2 (0 Critical, 0 Major, 31 Minor), review pass 3 (0 Critical, 0 Major, 26 Minor) and review pass 4 on fix pass 3's board `c84f00b8…` (0 Critical, 0 Major, 16 Minor) done, all dispositioned (below): passes 2, 3 and 4 found no Critical or Major. Fix pass 4 applied pass 4's two copper Minors as the reviewer trialled them (D110, D111; the copper diff is exactly the reviewer's `rec4`). Review pass 5 re-checked its board `cc044ea0…` in build integrity, planes and return paths, and routing (0 Critical, 0 Major, 3 Minor, all dispositioned below); the other five dimensions were not re-run on `cc044ea0…` (a further re-check is the owner's call) |

## Review pass 1 (board `429b6db4…`) and fix pass 1

Eight independent reviewers (pyro and arming, requirements traceability, RF, power / thermal / hot-plug, routing
simplicity, planes and return paths, DFM / fit / mechanical, build integrity), with the three-skeptic check on every
Critical or Major finding. Reports: `m3_design/assembly_review/sources/r8_review/pass1_*.md`. Result: **0 Critical,
1 Major, 38 Minor.** The gate passed on `429b6db4…`; the Major is a gap in the deviation list, not in the copper. Fix
pass 1 (R8_DECISIONS D85–D96; log `sources/r8_review/fix1_progress.md`, handoff `fix1_handoff.md`) changed the
generators, tables and tools only; `m3_design/r8_build.sh` rebuilds the result byte for byte (final board
`6600ef94…`, two consecutive builds).

| ID | Sev. | Skeptics | Finding (short) | Disposition |
|---|---|---|---|---|
| R8P1-REQUIREMENTS-01 | Major | Major / Major / Major | Deviation list omits whole M2 review categories (chain detours on nets without a pour, adjacency under 0.2 mm, extra vias), no "swept, none" | **Fixed.** The sweep is a script (`step9/m2_sweep.py`, D96) run on the final board; part C gains C11–C18 with locations, measured figures and reasons, part F states a "swept" line per M2 category, the owner summary is recounted. Copper where cheap (D91): four signal gaps opened (BUZZ_DRV / PULLPIN, I2C1_SCL / SDA, RADIO_NRST / CAM_MCU_RX's via, SERVO1_MCU / VLOGIC's via), three chain detours with a clean redraw redrawn (VLOGIC sense, USB_DM, ACT_GATE; CAM_5V's was built and reverted, it made an untidy pad entry); the rest recorded |
| R8P1-REQUIREMENTS-02 | Minor | — | Bootloader entry only by firmware jump; "radio held in reset in the bootloader" rests on firmware | **Fixed** (records): binding constraint D6.8, the binding note, F10's text, ORDERING §5's reset step repeated in the bootloader |
| R8P1-REQUIREMENTS-03 | Minor | — | J1's pin legends read across neighbouring pins ('4:SW' nearer J124.1) | **Fixed:** `r8_post.py` own-cell placement, J1's in the forward strip; gate `check_r8.terminal_legends` with a seeded test (D92) |
| R8P1-REQUIREMENTS-04 | Minor | — | BAT_ENABLE (U9 EN, megohm node) crosses PYRO_BLOCK; record says no signal crosses; latch not assessed | **Fixed** (records): M3_R8 corrected; "Pyro review observations" below carry the crossing, its neighbours and the latch analysis; ORDERING §5's switch cycles now require the board to turn off with the link in |
| R8P1-REQUIREMENTS-05 | Minor | — | Stale or inexact facts (PD9, U4 "under U1", J2 0.84 mm, 4.6 mm) | **Fixed:** PE9; "west of U1"; locating hole 0.84 / contact pads 1.32 mm; 3.9–10.6 mm (R167 3.86 mm) |
| R8P1-REQUIREMENTS-06 | Minor | — | AGENTS sets one review pass as the R8 ordering gate | **Fixed:** two consecutive passes (REQUIREMENTS "R8 acceptance") |
| R8P1-REQUIREMENTS-07 | Minor | — | STATUS's R7 section contradicts itself on pass 8 | **Fixed** |
| R8P1-REQUIREMENTS-08 | Minor | — | README presents R4 as current | **Fixed:** README points at STATUS / M3_R8: R8 candidate, R7 fallback, one pyro channel, 46 × 118 mm |
| R8P1-REQUIREMENTS-09 | Minor | — | P2's "about R6's level" and M2's poured-net list are R7's | **Fixed** |
| R8P1-REQUIREMENTS-10 | Minor | — | Per-via currents of the 7.7 A via fields not reported | **Fixed** with R8P1-POWER-01 (`dc_solve --via-currents`; M3_R8, MARGIN P1-9) |
| R8P1-PYRO-01 | Minor | — | Battery-live ACT_FET_S pour at rule F's 0.501 mm from J124.1 | **Fixed:** chamfer, 1.089 mm; gate `check_r8.battery_pyro` (BAT_IN / ACT_FET_S ≥ 1.0 mm from BUS / IGN, same layer) with a seeded test (D85). ARM1_SENSE via gap 0.301 mm kept (sense node; 0.2 mm of neck) |
| R8P1-PYRO-02 | Minor | — | RAW_ACT pour 0.696 mm from bare R127.1 (GATE_N), 0.501 from C127.1 | **Fixed (a):** chamfer, R127.1 1.115 mm, neck unchanged. **(b) not applied:** the C127.1 pair is benign (no fire) and its step costs 0.22 mm of neck; recorded below |
| R8P1-PYRO-03 | Minor | — | BAT_ENABLE in the block; step-9 survey missed new copper by the sense / gate pads | **Fixed** (records): observations table below; ORDERING §5 steps kept and extended |
| R8P1-PYRO-04 | Minor (not worth fixing) | — | GATE_N lane between the two sense lanes; hard-short gate ≈ 0.37 V | **Recorded:** screened by JLC's electrical test and the static gate; ORDERING §5 now repeats the static gate warm where convenient |
| R8P1-RF-01 | Minor | — | Unstitched 0.535 mm GND finger between RADIO_NSS and RADIO_SCK | **Fixed:** pour trim G7 (D90); the finger is gone (fingers below) |
| R8P1-RF-02 | Minor | — | R7's pass-4 RF dispositions (C11, P4-RF-02, C13) not carried | **Fixed** (records): note "R7 pass-4 RF items on R8" and rows C15 (fingers) and C16 (D30.2 / D31.2 solid). The optional F.Cu module-ground gate is not added: the F.Cu GND under both bodies is measured equal to R7's; where a trim lands stays ungated (corrected in fix pass 2, R8P2-INTEGRITY-05: no digest covers the F.Cu fill under the module bodies, see "R7 pass-4 RF items on R8") |
| R8P1-RF-03 | Minor | — | RF bench step probes PD9 (R7's NRST pin) | **Fixed:** PE9 (U1.39), R311.1, and RXEN at R312.1 |
| R8P1-RF-04 | Minor | — | Coexistence step never runs the GNSS with the camera supply on | **Fixed:** ORDERING §5 step extended (camera on, MCU at flight clock with QSPI logging, radio idle then keyed) |
| R8P1-POWER-01 | Minor | — | F4 record lacks the servo GND return and via-field currents | **Fixed** (tools, records): `dc_solve --window / --via-currents`, `run_dc.sh` DC_GND row; M3_R8 "DC solve" (D95) |
| R8P1-POWER-02 | Minor | — | The cited thermal-camera stall test is not in ORDERING §5 | **Fixed:** ORDERING §5 "7.7 A stall test" with the R8 hot spots and D12's estimates as pass criteria |
| R8P1-POWER-03 | Minor | — | U10's input bypass C83 17.5 mm of track from U10.1 | **Fixed:** C83 beside U10.1 / U10.2 (D88); D42 corrected |
| R8P1-POWER-04 | Minor | — | U9's D9 / C82 on a 5.5 mm stub beyond the trunk via (SLVSFC9C §8.4.1) | **Recorded, not reworked** (the reviewer: not worth a placement change on its own): an internal-fault margin (the camera has its own eFuse U7); deviation from §8.4.1 noted in M3_R8 |
| R8P1-POWER-05 | Minor | — | Single-via series links carry whole rails (3V3 In2 feed, RAW_PROTECTED at U9.6, camera feed, hold-up) | **Recorded, not reworked:** capacity adequate (≤ 9–19 °C barrel estimate, Inference); accepted single points per MARGIN R15, listed in M3_R8 |
| R8P1-POWER-06 | Minor | — | dc_solve docstring: through-hole pads "join their layers" | **Fixed:** docstring corrected (only vias join layers; pessimistic) |
| R8P1-ROUTING-01 | Minor | — | HSE_OUT folds back through its via | **Fixed:** via between Y1.3 and C26.1 (D86), 9.27 → 7.38 mm |
| R8P1-ROUTING-02 | Minor | — | Untidy entries on large pads (U9.5, C75.2, C75.1; U9.7) | **Fixed:** U9.5, C75.2, U9.7 (D94); C75.1's straddle recorded (C18); the M2 sweep reports pad-edge ends of any pad size (none) |
| R8P1-ROUTING-03 | Minor | — | VLOGIC sense via 0.6 mm at the DRC minimum from SERVO1_MCU | **Fixed:** 0.5 mm signal via, 0.20 mm (D91) |
| R8P1-ROUTING-04 | Minor | — | Cross-layer fold-backs neither gated nor listed | **Fixed** (records): C14 lists the via folds with reasons (the M2 sweep's `via_fold`); HSE_OUT's removable one is gone. Not gated: every remaining critical-net fold is a forced pad-order, keep-out or T-junction case |
| R8P1-PLANES-01 | Minor | — | C11-class fingers missing from the list; worst the radio-bus sliver | **Fixed:** G7 (D90); C15 lists the rest |
| R8P1-PLANES-02 | Minor | — | Reference audit covers 24 of 59 critical nets; ARM1_SENSE's split crossing unrecorded | **Fixed** (records): M3_R8 "Return paths" names the crossing and the audit's net set. The `--agents3` audit option is not added (no copper change; pass 1's full-set sampling is the measurement) |
| R8P1-PLANES-03 | Minor | — | In2 3V3 is the reference under U1's stubs and the sensors; unrecorded | **Fixed** (records): M3_R8 "Power" paragraph |
| R8P1-PLANES-04 | Minor | — | The servo GND return is unsolved; J1.2's spokes are its narrowest point | **Fixed** with R8P1-POWER-01 |
| R8P1-DFM-01 | Minor | — | U30's paste prints over the limiter vias; VLOGIC via ring on C7.1's paste | **Fixed:** vias at R7's y 8.3, VLOGIC via moved; gate `check_r8.via_paste` with a seeded test (D87) |
| R8P1-DFM-02 | Minor | — | Left forward tab on the 7.7 A band | **Fixed:** tab at y 112.5–117.5 (D93) |
| R8P1-DFM-03 | Minor | — | Solid connections kept on moved THT GND pins | **Fixed for J3.1 / J3.4** (thermal); J123.2 was kept solid on a DRC `starved_thermal` that held only on the step-6 board; **fix pass 2 relieved it on the final copper** (R8P2-DFM-01, D101); ORDERING §4 corrected (D89) |
| R8P1-DFM-04 | Minor | — | Documentation details (J2 hole, C84 "tallest", U4 "under U1", D35 / D39 step-4 tables) | **Fixed** |
| R8P1-INTEGRITY-01 | Minor | — | Records present relaxed or skipped plan checks as passed | **Fixed** (records): step table, hard gates, AGENTS / F10 / M3_R8 strip wording, D5 and D10 in the owner summary's decision list |
| R8P1-INTEGRITY-02 | Minor | — | F4 neck limits not held by the build; DC evidence not SHA-bound | **Fixed:** `r8_build.sh` runs `run_dc.sh` at 0.1 mm after step 7; `dc_solve.py` prints the board SHA-256 first (D95) |
| R8P1-INTEGRITY-03 | Minor | — | R8 exists only as an uncommitted worktree | **Not done: owner action.** AGENTS allows commits only when the owner asks, and the fix-pass brief said not to commit. The pass-1 generator state was not preserved (fix pass 1 rewrote it in place; `fix1_handoff.md` describes the deltas); see R8P2-INTEGRITY-03 |

## Review pass 2 (board `6600ef94…`) and fix pass 2

Eight independent reviewers, the same angles as pass 1 (`sources/r8_review/pass2_*.md`). Result: **0 Critical,
0 Major, 31 Minor**, so no finding needed the three-skeptic check ("—" below). Pass 2 is the first pass with no Critical or
Major; R8 acceptance needs pass 3 to find none as well. Fix pass 2 (R8_DECISIONS D97–D105; log
`sources/r8_review/fix2_progress.md`, handoff `fix2_handoff.md`) changed the generators, tables and tools only;
`m3_design/r8_build.sh` rebuilds the result byte for byte (final board `990c8040…`, two consecutive builds). "Fixed
differently" means the reviewer's edit failed a gate and a legal one was used instead.

| ID | Sev. | Skeptics | Finding (short) | Disposition |
|---|---|---|---|---|
| R8P2-PYRO-01 | Minor | — | `battery_pyro` measured BAT_IN / ACT_FET_S against BUS / IGN only, not the drain PYRO1_OUT, where battery copper fires an armed igniter with the switch open | **Fixed:** `check_r8.ARM_SIDE` adds PYRO1_OUT; seeded drain case in `test_r8_check` (fails with the old set); D85 / D103, M3_R8, REQUIREMENTS F8. The board passes unchanged: nearest 1.089 mm (ACT_FET_S–J124.1), the drain's nearest battery copper 3.562 mm (R82.1–J121.1) |
| R8P2-PYRO-02 | Minor | — | M3_R8 called GND beside armed copper "the safe direction"; on the drain it bypasses Q124; two step-7 GND vias 0.528 / 0.537 mm from drain copper | **Fixed (records):** M3_R8 corrected; "Pyro review observations" gains the GND row. The optional `make_ground` 1.0 mm from PYRO1_OUT is not applied: the GND pour edge stays at rule D's 0.50 mm from the bare drain pads (R7's accepted geometry), so moving two tented vias gains nothing (the reviewer's assessment); the plug-out cold test and the static gate screen a drain-to-GND path |
| R8P2-PYRO-03 | Minor | — | The bootloader-jump binding constraint did not put PE4 (the pyro gate drive) low | **Fixed (records):** `binding_note.py` constraint (PE4 low first, or the GPIOE reset that returns it to analog so R127 holds the gate off), note regenerated on `990c8040…`, D6.8, REQUIREMENTS F10 |
| R8P2-PYRO-04 | Minor (not worth fixing) | — | ACT_GATE's chamfered stub passes 0.264 mm from bare C120.1 (ACT_FET_S) | **Accepted, recorded** ("Pyro review observations"): a bridge holds the actuator switch off (V_GS → 0), the fail-safe direction; the track is masked and C120's own pads sit 0.50 mm apart by design |
| R8P2-REQUIREMENTS-01 | Minor | — | C12's adjacency sweep left out pad-to-copper gaps; R7 C15 #1 / #6 dropped; BAT_ENABLE–BAT_IN latch pairs at 0.18 mm recorded nowhere | **Fixed:** `m2_sweep.py adjacency_pad` (D104); C12 lists the pad rows with what a short does (R7 C15 #1 / #6 restored); the BAT_ENABLE–BAT_IN pairs are in the pyro observations (latch class, screened by ORDERING §5's switch-off step); R81's two pairs are gone (D100) |
| R8P2-REQUIREMENTS-02 | Minor | — | "A second consecutive review pass" understated the condition | **Fixed:** this record's head and the review-history row: passes 2 and 3 at least |
| R8P2-REQUIREMENTS-03 | Minor | — | D5 called an owner decision; D70 missing from the owner summary's decision list | **Fixed:** hard-gate rows (D5, D70) and the owner summary |
| R8P2-REQUIREMENTS-04 | Minor | — | The C2 scorecard miss had no stated cause | **Fixed:** C19 gives each information category's measured reason and what a search cleared (C2 93 → 90) |
| R8P2-REQUIREMENTS-05 | Minor | — | README dropped the Ø50.8 mm coupler | **Fixed** (README) |
| R8P2-REQUIREMENTS-06 | Minor | — | Six record mismatches | **Fixed:** (a) MARGIN's BAT_IN via count (4 over 0.5 A); (b) AGENTS adds the 24 h cost and stock run; (c) REQUIREMENTS M2's relief-exception pointer names C17; (d) F8 names `battery_pyro`; (e) 21.4 °C in ORDERING; (f) STATUS dates in one convention and R7's ORDERING on branch `m3-assy-r7` |
| R8P2-POWER-01 | Minor | — | ORDERING §5's stall test could not judge D12 (FET-dominated readings, undefined duration, J1.2's top hidden, stale 21.5 °C) | **Fixed:** ORDERING §5 rewritten (steady state or a stated flight stall; RAW_ACT neck ≤ 17.5 °C; FET tabs and the copper beside them ≤ about 29 °C rise per MARGIN R1; BAT_IN / ACT_FET_S against D12 as information; J1.2 from the bottom), D105, F4 / M3_R8 sentence |
| R8P2-POWER-02 | Minor | — | A dead-end In2 BAT_IN area put unfused battery copper at the east and forward edges, the right tab and an M3 hole | **Fixed** (D97): In2 BAT_IN 505.6 → 229.6 mm²; the right forward tab and the hole (42, 114.4) GND on all four layers; BAT_IN neck 6.99 mm (unchanged), R 0.42 → 0.45 mΩ; ORDERING §3 / §7 |
| R8P2-POWER-03 | Minor | — | U13's capacitors 5.6 / 6.75 mm of track from its pins (TI SBVS186H §10.1) | **Accepted, recorded** (M3_R8 Power): §8.1.1's stability window is met (the track adds about 11 mΩ / 5 nH, Inference), CAM_IO_3V3 carries mA; a U13 / C92 re-placement reopens the camera stage for no measurable gain |
| R8P2-POWER-04 | Minor | — | The build's DC gate and `dc_solve --window / --via-currents` have no seeded test | **Accepted** (with R8P2-INTEGRITY-04): the fail path was seeded by hand in passes 1 and 2 (NECK FAIL, exit 1 under `set -e`); recorded as a test gap for a later tools pass |
| R8P2-POWER-05 | Minor | — | Record slips: BAT_IN via count, "nearest pad edge" figures that are centre to centre, a copied fold reason | **Fixed:** (a) as REQUIREMENTS-06(a); (b) M3_R8, D76, STATUS and this record now say centre to centre, with the pad-edge range 2.0–8.4 mm; (c) C14's (34.4, 69.65) row names the In2 3V3 region's only feed |
| R8P2-ROUTING-01 | Minor | — | Four 0.150 mm pairs open with the board's 0.5 mm via (same drill) | **Fixed** (D98): C12's 0.150 mm pairs 14 → 10, pairs 32 → 29 |
| R8P2-ROUTING-02 | Minor | — | The battery-live BAT_IN feed threads R81's pads at 0.170 / 0.180 mm | **Fixed differently** (D100): the reviewer's `r81w` fails the legaliser (R81's courtyard within 1.5 mm of J121.1, R5 L10); R81 stands vertical west of the spine on a stub; the feed threads no part and keeps ≥ 0.20 mm from other nets |
| R8P2-ROUTING-03 | Minor | — | The sweep and C12 omit every track / via-to-pad gap | **Fixed** with REQUIREMENTS-01 (D104); C12's scope sentence and part F corrected; Q120.9 in the pyro observations' BAT_ENABLE row |
| R8P2-ROUTING-04 | Minor | — | A 0.247 mm jog inside C83.2 on the D4.2 pocket's GND link | **Fixed differently** (D99): moving C83 0.175 mm forward fails R5 L10 against J3.1 (and east overlaps U10; U10 aft lands U10.3 on V_D's via); the link is split into two straight tracks: C83.2's instances 3 → 1 (pad_end_offcentre 0.175 mm), no micro-segment |
| R8P2-PLANES-01 | Minor | — | U9's GND terminal 14.1 mm of copper from a GND via; C15's "no via fits" untrue there | **Fixed** (D102): `make_ground.py`'s pad stage puts a via at (44.65, 86.775): U9.8 2.54 mm, R84.2 0.64, C81.2 3.51 mm; C15 and M3_R8 Power (SLVSFC9C §8.4.1) |
| R8P2-PLANES-02 | Minor | — | M3_R8 "Ground" still gave 90.65 % and one slot | **Fixed:** M3_R8 gives the final board's 90.50 % and four slots |
| R8P2-PLANES-03 | Minor (not worth fixing) | — | No gate or record measured GND-pad copper reach | **Fixed in part:** D102's stage now applies it to every IC GND pad at generation; C15 names the pads each listed piece serves and records J9.2 6.92, U13.2 9.28, Q122.2 / R123.2 12.42 / 12.98 mm (no legal spot their copper reaches) |
| R8P2-DFM-01 | Minor | — | J123.2 kept solid on a `starved_thermal` the final board does not reproduce | **Fixed** (D101): relieved in `r8_ground.py` on the final copper (B.Cu 2 spokes, F.Cu and In1 4); D89, C17, the `r8_pcb.py` comment and ORDERING §4 corrected (J122: the 7.7 A return; J122.3 also starved on F.Cu) |
| R8P2-DFM-02 | Minor (not worth fixing) | — | J1's `1:BAT+` legend sits aft of the terminal, the others on the wire-entry strip | **Accepted, not changed:** `terminal_legends` passes (nearest its own pin), cosmetic |
| R8P2-DFM-03 | Minor | — | ORDERING's tab table names J9 for the right aft tab (J31 is 11.4 mm away, left out of the window search); C83 not named in the J3 hand-finish steps | **Fixed** (ORDERING §3 note; §4 and §5 J3 steps name C83) |
| R8P2-INTEGRITY-01 | Minor | — | J123.2's exception rested on a step-6 DRC result | **Fixed** with DFM-01 |
| R8P2-INTEGRITY-02 | Minor | — | `via_paste` described as R7's ViaCheck rule but 0.1 mm looser on the ring | **Fixed (records):** `check_r8` docstring and comment, D87, the hard-gate row; by ViaCheck's rule 13 via–aperture pairs (12 vias) on `990c8040…`, 14 on `6600ef94…`, R7 5. Tightening the ring clause is left to the DFM review (all own-net, tented) |
| R8P2-INTEGRITY-03 | Minor | — | R8 still uncommitted; pass 1's generator state lost | **Not done: owner action** (no commit allowed). Recorded: neither reviewed state survives as a commit; `fix2_baseline_sha256.txt` holds the SHA-256 of the 222 changed / untracked files fix pass 2 started from, and `fix2_handoff.md` lists every file it changed. Commit or tag before pass 3 and record the commit beside `990c8040…` |
| R8P2-INTEGRITY-04 | Minor (not worth fixing on its own) | — | The build's DC neck gate has no automated test | **Accepted** (as POWER-04) |
| R8P2-INTEGRITY-05 | Minor | — | STATUS dated fix pass 1 2026-10-20; RF-02's reason contradicted the RF note; four fix-1 evidence files lacked the board SHA | **Fixed:** STATUS; the R8P1-RF-02 row; the four files re-run on `6600ef94…` (identical) and given a `board_sha256` field |
| R8P2-RF-01 | Minor (not worth fixing) | — | The limiter via's GND partner given as (9.025, 8.325) 1.39 mm; the nearest is (10.37, 7.08) 1.22 mm | **Fixed (records):** M3_R8 and route_check's A3 reason text (no gated figure) |

## Review pass 3 (board `990c8040…`) and fix pass 3

Eight independent reviewers, the same angles as passes 1 and 2 (`sources/r8_review/pass3_*.md`). Result: **0 Critical,
0 Major, 26 Minor**, so no finding needed the three-skeptic check ("—" below), and **passes 2 and 3 are two consecutive
passes with no Critical or Major** (r8_plan §4's stop condition, REQUIREMENTS "R8 acceptance"). Fix pass 3 (R8_DECISIONS
D106–D109 and corrections to D6.8, D76, D87, D98, D105; log `sources/r8_review/fix3_progress.md`, handoff
`fix3_handoff.md`) changed the generators, tables and tools only; `m3_design/r8_build.sh` rebuilds the result byte for byte
(final board `c84f00b8…`, two consecutive builds, and a third on the final generator state). Its three copper edits are the routing reviewer's own variants, each
DRC-, gate- and contract-clean in that review's trial and again in both builds; the final board itself had not been
reviewed then (review pass 4 re-checked it, below). "Reviewer's call" is the reviewer's own "worth fixing"
mark; "Fixed (records)" changes no copper.

| ID | Sev. | Skeptics | Reviewer's call | Finding (short) | Disposition |
|---|---|---|---|---|---|
| R8P3-ROUTING-01 | Minor | — | worth fixing | USB_LIMITED (5 V) 0.150 mm from CAM_PWR_EN and 0.180 mm from both bare pads of R172 (R172.2: PB0, no series resistor) | **Fixed** (D106): trunk y 37.25 → 37.3, R172 and its lane x 30.6 → 30.65: 0.200 / 0.230 / 0.230 mm; C12 #5 and C12b #20 / #21 gone; L10_EXCEPT's R172 figure 0.635 → 0.685 mm |
| R8P3-ROUTING-02 | Minor | — | worth fixing | R165's BAT_ENABLE via drawn with the 0.6 mm power via, 0.180 mm from Q120's bare BAT_IN drain pad | **Fixed** (D108): the board's 0.5 mm signal via, 0.23 mm; C12b #18 gone; the ViaCheck list 13 → 12 pairs |
| R8P3-ROUTING-03 | Minor | — | worth fixing | CAM_PWR_EN's lower leg has a clean redraw 1.98 mm shorter, hidden by RedrawCheck's 0.01 mm margin | **Fixed** (D107): one 45° run into R74.1 (22.12 → 20.15 mm, C11); `m2_sweep.py margin_free` searches at DRC's threshold (part F: nothing else found) |
| R8P3-PYRO-01 | Minor | — | not worth fixing | The R120.2 GND via is not ACT_GATE's nearest GND copper; fix pass 2's candidate gains nothing | **Closed, records** (D109): the pour figures (0.151 mm at five bare ACT_GATE / ACT_DRV pads, R7's class) in C12b, the pyro observations, M3_R8 and `fix2_handoff.md`; candidate dropped; a GND-to-gate zone rule offered as an owner option |
| R8P3-PYRO-02 | Minor | — | worth fixing (records) | R81.2, a bare GND pad since D100, is the drain's nearest bare GND pad (1.825 mm from J121.1); the GND row omitted it | **Fixed (records):** pyro observations' GND row and closing sentence, M3_R8 |
| R8P3-PLANES-01 | Minor | — | worth fixing (records) | As PYRO-01 (the five pads, the pour at 0.150 mm) | **Fixed (records)** with PYRO-01 (D109) |
| R8P3-PLANES-02 | Minor | — | worth fixing (records) | The P3b scorecard row named three of the four In1 slots and said no critical track crosses them | **Fixed (records):** the row names the SPI1 / IMU_CS cluster and SPI1_SCK's 34 edge samples over it |
| R8P3-RF-01 | Minor | — | worth fixing | The bootloader-jump step allowed a GPIOE reset first, which puts the SX1262 in reset (BUSY high) before the sleep command | **Fixed (records):** the order is PE4 low; SX1262 asleep and PE9 low; GPIOE reset last (or PE4 kept low, PE9 to analog): `binding_note.py` (note regenerated on `c84f00b8…`), D6.8, F10, M3_R8, ORDERING §5 |
| R8P3-RF-02 | Minor | — | worth fixing | The coexistence step named only the 25 MHz spur near L1; 25 MHz × 47 = 1175.000 MHz lies in the L5 / E5a / B2a band the MAX-F10S always tracks | **Fixed (records):** ORDERING §5 (both spurs; C/N0 per signal, UBX-NAV-SIG) and M3_R8 RF |
| R8P3-RF-03 | Minor | — | not worth fixing | D98 and an `r8_power.py` comment call R78.2's GND via C76.2's | **Fixed (records):** D98, D87's correction, the `r8_power.py` comments, `fix2_handoff.md`, `fix2_progress.md` |
| R8P3-DFM-01 | Minor | — | worth fixing (records) | As PYRO-01; also J1.4 (via 0.189 mm, pour 0.151 mm) and J123.1 (via 0.200 mm, pour 0.150 mm) | **Fixed (records)** with PYRO-01 (D109): C12b's J1.4 row and the note under C12b |
| R8P3-DFM-02 | Minor | — | not worth fixing | `via_paste`'s ring clause (0 mm) is looser than R7's ViaCheck (0.1 mm): 13 own-net tented pairs with a sub-0.10 mm mask web | **Accepted, recorded:** 12 pairs at 11 vias since D108 (worst 0.025 mm, C90.1, as R7's worst); all own-net and tented, so a lost web wets a same-net ring and cannot short anything; the gate stays as it is (the hard-gate row); the optional ratchet was not added |
| R8P3-DFM-03 | Minor | — | not worth fixing | Q123's library pin-1 dot overlaps R162.2's mask opening by 0.065 mm (0.012 mm²) | **Accepted, recorded** as C20 (the Gerber export clips it; R162's move waits for the next buzzer-group placement change) |
| R8P3-INTEGRITY-01 | Minor | — | worth fixing | R78.2's GND via recorded as C76.2's, so D87's correction misnamed the via that left the ViaCheck list | **Fixed (records)** with RF-03 |
| R8P3-INTEGRITY-02 | Minor | — | worth fixing | "272 tests OK" rested on a log that shows `test_fab_validation` failing; the reproduce block ran the tests before `r8_fab.sh` | **Fixed:** `r8_fab.sh` before the tests in `fix2_handoff.md`'s and `fix3_handoff.md`'s reproduce blocks; `test_fab_validation`'s docstring says so; fix pass 3's post-fab test log kept (`step9/evidence/fix3_tests.txt`) |
| R8P3-INTEGRITY-03 | Minor | — | worth fixing (records) | As PYRO-01 | **Fixed (records)** with PYRO-01 (D109) |
| R8P3-INTEGRITY-04 | Minor | — | worth fixing (owner action) | R8 still uncommitted at pass 3 | **Not done: owner action** (no commit allowed). The coordinator kept a backup of the `990c8040…` state (session scratchpad `r8_backup_990c8040/`); fix pass 3 recorded the SHA-256 of every changed or untracked file it started from (`sources/r8_review/fix3_baseline_sha256.txt`) and its code / table diff (`fix3_generators.diff`) |
| R8P3-REQUIREMENTS-01 | Minor | — | worth fixing | ORDERING §5 lacked three checks STATUS attributes to it: the pyro gate low in the bootloader (D6.8), the camera buck's remote sense under a load step (D41), the IMU signs with the new lever arm | **Fixed (records):** ORDERING §5 gains all three (TP122 below 0.1 V and the static gate in the bootloader; CAM_5V at J9.1 under a 0.1 → 1 A step; the gyro / accelerometer signs) |
| R8P3-REQUIREMENTS-02 | Minor | — | worth fixing | The ACT_GATE item misdescribed (the pour is nearer) and screened by a conditional step | **Fixed (records)** with PYRO-01 (D109): the screens named are the 20 power-switch cycles and the hot RAW_ACT check |
| R8P3-REQUIREMENTS-03 | Minor | — | worth fixing | The owner summary's decision list left out D51 | **Fixed** (owner summary) |
| R8P3-REQUIREMENTS-04 | Minor | — | worth fixing | (a) C12 #13 called a false "disarmed" reading the safe direction; (b) M3's R8 sentence hid that the cost report binds the step-9 CPL | **Fixed (records):** C12 #12 (pass 3's #13; #10 since fix pass 4); REQUIREMENTS M3 |
| R8P3-POWER-01 | Minor | — | worth fixing | The stall test's RAW_ACT neck sits 0.34 / 0.86 mm from J122.3 / J122.2, whose contacts heat the same pour | **Fixed (records):** read the neck at y 83.35–86.25 (≥ 3 mm from J122), J122's contacts recorded; ORDERING §5, D105's correction, M3_R8 |
| R8P3-POWER-02 | Minor | — | worth fixing | U11's IN1 via (35.25, 60.5) is an undocumented single-via point on the logic supply | **Fixed (records):** M3_R8's single-point list adds it and the 3V3A hop pair (MARGIN R15) |
| R8P3-POWER-03 | Minor | — | not worth fixing | As PYRO-01 | **Closed, records** with PYRO-01 (D109) |
| R8P3-POWER-04 | Minor | — | not worth fixing on its own | F9's pad-edge figures treated J1.1's square pad as round (2.0–8.4 mm; true 1.9–7.8 mm); `hotplug_feed.py`'s docstring stale | **Fixed (records):** re-measured on `c84f00b8…` (R167 1.91 … C96 7.82 mm) in M3_R8, D76, this record, STATUS; the docstring (no model change) |
| R8P3-POWER-05 | Minor | — | not worth fixing | The left y 63–68 tab has In2 3V3 to 0.5 mm from the edge, unrecorded | **Fixed (records):** ORDERING §3 |

## Review pass 4 (board `c84f00b8…`), its records pass and fix pass 4

Eight independent reviewers, the same angles as passes 1–3 (`sources/r8_review/pass4_*.md`), on fix pass 3's final board
`c84f00b8…`: the re-check offered after fix pass 3. Each confirmed the board's SHA-256 before and after and found the
repository unchanged by its review; the gate exits 0; the build reproduces the whole tree byte for byte from a fresh clone
of 431025d; every pass-3 finding is closed or properly dispositioned (R8P3-INTEGRITY-04's commit is carried as
R8P4-INTEGRITY-01); fix pass 3's three copper edits break no requirement row, introduce no new rule instance and tighten
two gates, loosening none. Result: **0 Critical, 0 Major, 16 Minor**, so no finding needed the three-skeptic check ("—"
below). Passes 2 and 3 found no Critical or Major; pass 4 re-checked fix pass 3's board with the same result, so the
final board is itself reviewed.

The records pass after it (no fix-pass number and no D-number: it changes no generator, table, placement, copper,
schematic or build output) applied the record, procedure and tool-comment corrections, and the one evidence-tool
addition PYRO-01 asks for. Two Minors needed copper (ROUTING-01 / -02): the records pass left them open and in the
deviation list (C12 #5 / #6, C21), and fix pass 4 applied them (below). Files changed by the records pass: ORDERING (§1 status, §4 CPL label, §5 bootloader step,
coexistence, stall test), M3_R8, this record, STATUS, README, AGENTS, REQUIREMENTS (M2's J2 sentence), R8_DECISIONS (D6.8's
bench sentence, D101, D105's correction), `fix3_handoff.md` (R172's size), `step9/requalify.py` (rule G) and
`step9/evidence/fix3_requalify_r8.json` (its G entry; every other key re-ran equal). After it, `tools/check.sh` exits 0
and the board (`c84f00b8…`), netlist, the 15 sheets, `r8_ground.tsv` and the fab package are byte-identical to before
it. "Reviewer's call" is the reviewer's own "worth fixing" mark.

**Fix pass 4** (D110, D111; `sources/r8_review/fix4_handoff.md`, log `fix4_progress.md`) then applied, through the
generators and tables only, the two copper Minors as the routing reviewer trialled them (`fence2` and `r87`, together
the reviewer's `rec4`), and the four text items the records pass had recorded but not changed (RF-02, POWER-02, DFM-02,
INTEGRITY-02). Its board is `cc044ea0…` (two byte-identical builds; `tools/check.sh` exit 0); the copper diff against
`c84f00b8…` is exactly `rec4`'s: three tracks each of RADIO_RXEN, RADIO_BUSY and RADIO_MISO_MCU, three GND vias moved
0.05 mm, USB_LIMITED's branch (−4 / +3 tracks); no part, designator or silkscreen item moved. After it every pass-4
finding is fixed except INTEGRITY-01 (the commit, an owner action). The fix-pass-4 board had not itself been reviewed
then (review pass 5 re-checked it in three dimensions, below).

| ID | Sev. | Skeptics | Reviewer's call | Finding (short) | Disposition |
|---|---|---|---|---|---|
| R8P4-PYRO-01 | Minor | — | worth fixing (records and tool) | `step9/requalify.py` (and so `fix3_requalify_r8.json` and M3_R8's per-rule table) covered 8 of the DRU's 9 pyro rules, leaving out G (gate nets in the block, 0.3 mm), the one rule whose copper sits at its minimum: the GATE_N lane x 18.75 0.300 mm from the PYRO1_CONT lane x 19.25 on B.Cu, the whole 33.5 mm GATE_N segment counting because it reaches into PYRO_BLOCK (R7 0.316 mm). Screened elsewhere (M3_R8's exits, R8P1-PYRO-04, the warm static gate); DRC holds G; no board defect | **Fixed (tool, records):** G in `requalify.py`'s rules (a gate-net item that intersects the PYRO_BLOCK rule area, tested on the board's own outline as the DRU's `A.intersectsArea`; B not GND / RAW_ACT / BUS / IGN / OUT / a gate net; Q124's own pads exempt). Re-run on `c84f00b8…`: G 0.300 mm, margin 0, GATE_N track (18.75, 87.78) to PYRO1_CONT (19.25, 58.1–87.0), B.Cu, 6 pairs within 0.1 mm of the minimum; every other section equal to `fix3_requalify_r8.json`, which gained the G entry. On R7 `c872a3d3…` the tool gives 0.316 mm (GATE_N to SERVO2_MCU, In2), as the reviewer measured. M3_R8's table gains the G row; the "Pyro exits and rule margins" row above now lists every rule |
| R8P4-REQUIREMENTS-01 | Minor | — | worth fixing | The bootloader pyro-gate check (fix pass 3) sat in the RF bullet's radio-reset step, run once before flight, outside the pyro-gate list repeated after any firmware change, though the jump's preparation (D6.8) is firmware; it pointed to the static gate "below" (it is above) and did not confirm the board was still in the bootloader once USB was unplugged | **Fixed (procedure, records):** ORDERING §5's pyro-gate list gains a "Bootloader" step: after the jump, link out, TP122 below 0.1 V; unplug USB and confirm the bootloader (RADIO_NRST at R311.1 still below 0.66 V; Inference: the application releases NRST when it starts the radio, binding constraint 2); then the static gate armed. The RF bullet points to it ("above"); D6.8's bench sentence names the list |
| R8P4-REQUIREMENTS-02 | Minor | — | worth fixing | C12b #3 ("false launch detects while the buzzer sounds"), D101 ("a false launch detect") and AGENTS §1 ("Pull-pin (launch detect)") gave the pull-pin a role F9 / FMEA F-7 removed: it is an advisory pad witness, ignored after launch | **Fixed (records):** C12b #3 (a false or toggling advisory witness that can upset the ground PAD_ARMED → READY gate; never a launch detect; no fire path), D101 ("a false advisory witness, F9"), AGENTS ("Pull-pin (advisory pad witness, F9)"). The board side was right (BUZZ_OUT swings 0–3.3 V; no overvoltage on PC14) |
| R8P4-REQUIREMENTS-03 | Minor | — | worth fixing | Six figures or labels stale or ambiguous after fix pass 3 | **Fixed (records):** (a) M3_R8 "1497.6 mm of signal track (… fix pass 2 1499.6) … 1379.9 mm of it drawn by the nine family modules"; (b) the scorecard header "R8 (fix pass 3)"; (c) C4 1752.2 mm (fix pass 2 1752.5); (d) the owner summary "33 close pad / copper pairs (29 listed, 4 fine-pitch own-part escapes counted)"; (e) REQUIREMENTS M2 "fix passes 1–3 moved no via near J2"; (f) ORDERING §4 "(R8 board, fix pass 3; the same figures since step 8)" |
| R8P4-REQUIREMENTS-04 | Minor | — | worth fixing | README and ORDERING stated R8's review status differently from STATUS, AGENTS and this record (README omitted that `c84f00b8…` was unreviewed; ORDERING called the review loop open) | **Fixed (records):** one sentence in all five: passes 2 and 3 found no Critical or Major; pass 4 re-checked fix pass 3's board `c84f00b8…` (0 Critical, 0 Major, 16 Minor); still open: the owner's acceptance of the deviation list, U4 consigned, JLC's tab acceptance and a cost and stock run within 24 h |
| R8P4-RF-01 | Minor | — | worth fixing | ORDERING §5's coexistence step records only C/N0 changes between conditions, but the HSE runs in every condition and the radio's 32 MHz crystal in every one but sleep or reset, so a steady in-band spur sits in every baseline: the named HSE spurs (1575.000, 1175.000 MHz) and the unnamed radio-crystal 32 MHz × 37 = 1184.000 MHz (7.55 MHz from L5 / E5a / B2a, inside its main lobe); the UBX-MON-SPAN check R7's coexistence acceptance relied on was never in any ORDERING. Spur levels unknown (Inference) | **Fixed (procedure, records; no board or gate change):** ORDERING §5: UBX-MON-SPAN of both RF blocks in every condition with max hold, noting peaks at 1575.000, 1175.000, 1184.000 and 1568.000 MHz or any other against the noise floor (MAX-F10S IM §4.2.3); a radio-asleep or held-in-reset condition against one in RX (crystal on, not keyed); C/N0 per signal against a reference receiver (splitter or same place), CFG-ITFM / UBX-SEC-SIG jammingState optional. M3_R8 RF names the 32 MHz × 37 and × 49 harmonics beside the HSE's |
| R8P4-RF-02 | Minor | — | not worth fixing | ORDERING §5 gives U8's distances (13.5 mm from U31, 24.8 mm from U30) for the whole camera supply U7 / U8 / L3; U7 (the camera eFuse) is 9.41 / 17.98 mm, L3 17.53 / 26.07 mm. M3_R8's RF table is right | **Fixed (records, fix pass 4):** ORDERING §5 now gives the camera buck U8 / L3 13.5 / 17.5 mm from U31 and 24.8 / 26.1 mm from U30, courtyard to courtyard, and U7 (the camera eFuse, not a switcher) 9.4 / 18.0 mm, as M3_R8's RF table does (fix pass 4 moved no part). No bench consequence |
| R8P4-POWER-01 | Minor | — | worth fixing (records) | Fix pass 3 moved the stall test's RAW_ACT reading to the neck's forward window, clear of J122's contact heat, but that window carries the least current: 0.83 A/mm in F.Cu (0.1 mm solve), about 0.63 of the 1.31 A/mm D12's 17.5 °C assumes, because the two RAW_ACT vias inside it take 1.26 A down to In2; the aft end beside J122 carries about 1.6 A/mm. J122, the one 7.7 A part whose rating rests on no datasheet curve, was imaged without a pass line | **Fixed (procedure, records; no copper):** ORDERING §5's stall test, D105's correction and M3_R8 "DC solve" state the window's loose bound; the neck's hottest pixel over its whole cut box and the aft end are recorded as information; J122 passes at a hottest pin or housing rise ≤ 30 K at 7.7 A, steady state (MARGIN_PRESCRIPTION's reading of the maker's 3 A per contact as a 30 K rise; about 1.9 A per contact here) |
| R8P4-POWER-02 | Minor | — | not worth fixing | Twelve 0805 / 1206 capacitor GND pads (C6.2–C11.2, C80.2, C96.2, C150.2, C151.2, C310.2, C91.2) join the outer GND pours through 0.3 mm thermal spokes, where the DRU comment says only 0402 / 0603 pads do (R6's `r6_pcb.py` widened the rule to R / C GND pads up to 2.0 mm; R7 has the same twelve) | **Fixed (records, fix pass 4):** M3_R8 "Ground" names the rule as built: the DRU's "Small GND pad thermal relief" (0.25 mm gap, 0.3 mm spokes) applies to every SMD GND pad given a local thermal connection, which R6's `r6_pcb.py` gave every R / C GND pad up to 2.0 mm (R7 and R8 carry it), so these twelve pads are on spokes although the DRU comment says 0402 / 0603 only; the same twelve on `cc044ea0…` (measured); about 0.05 nH and 0.1 mΩ per pad (Inference), negligible against U2's input loop and F9's harness; no pad starved (DRC 0, fewest spokes 2, C10.2). The DRU comment stays as it is: the file is SHA-pinned by `check_actuators`. Not a defect |
| R8P4-ROUTING-01 | Minor | — | worth fixing (copper) | Below the fence (`r8_route_rf.py` l. 77–86) the radio trio RXEN / BUSY / MISO sits off-centre in its opening (RXEN 0.25 mm from the west via, MISO 0.150 mm from the east one), so RADIO_MISO_MCU (x 21.6) and RADIO_MOSI (x 22.6) are each 0.150 mm from two GND vias, the fence via (22.1, 23.3) and spike (d)'s stitch via (22.1, 26.7); C12 named only the fence via and called the pair "not cheap to open" | **Fixed (fix pass 4, D110; copper)** with the reviewer's trialled `fence2`: `r8_route_rf.py` puts the trio's below-fence lanes on x 20.5 / 21.0 / 21.5 with a 0.5 mm step (y 22.500 / 22.707 / 22.914; the in-strip lanes and the 45° runs to U1 on the same lines); `step7/make_ground.py` moves the fence vias x 20.00 / 22.10 → 19.95 / 22.05 and the stitch via (22.10, 26.70) → (22.05, 26.70); `r8_ground.tsv` regenerated from the step-6 board (those three rows; one cover row reordered, same coordinates). Measured on `cc044ea0…`: RXEN–(19.95, 23.3), MISO_MCU and MOSI to (22.05, 23.3) and (22.05, 26.7) all 0.200 mm (were 0.250 / 0.150 / 0.150); fence openings 1.75 (no lane) / 2.10 / 2.10 mm (D16; `check_r8` fence, strip GND reach and F10 OK); the rf family 436.6 → 436.9 mm of 445; M2 sweep: track / via net pairs under 0.2 mm 28 → 26 and 0.150 mm pairs 9 → 7 (exactly GND / RADIO_MISO_MCU and GND / RADIO_MOSI left), everything else equal; the trio's step knee 0.40 → 0.50 mm. C12 #5 / #6 are removed from the list |
| R8P4-ROUTING-02 | Minor | — | worth fixing (copper) | `r8_power.py` l. 324 draws USB_LIMITED's 0.25 mm branch to R87.1 (the OVLO divider top) from C98.1's centre, (35.25, 56.2) → (32.7, 56.2) → (32.2, 56.7) → (32.2, 57.775), 4.33 mm: it leaves at 45° to the trunk's own diagonal into C98.1 (the board's only R8-new acute branch pair; R133.1 and Q30.2 are rigid R7 copper) and runs 2.55 mm back west 0.9 mm under the y 55.3 trunk (1.65 mm of parallel same-net copper); route_check passes it because the apex lies 0.037 mm inside C98.1's pad | **Fixed (fix pass 4, D111; copper)** with the reviewer's trialled `r87`: `r8_power.py` draws the trunk through (32.2, 55.3) and R87.1's branch as the T drop (32.2, 55.3) → (32.2, 57.775). Measured on `cc044ea0…`: USB_LIMITED's B.Cu 51.44 → 49.59 mm (−1.86), its route ratio 1.28 → 1.23; acute pairs at a node 3 → 2 (the two left, R133.1 and Q30.2, rigid R7 copper); the 1.65 mm parallel run gone; R87.1 entered axially from the north to its centre; every USB_LIMITED clearance within 0.6 mm unchanged; route_check one information instance more (width_change_junction at the T, 0.4 / 0.25 mm: C2 90 → 91, C19); step 7 put no via in the freed B.Cu; USB_LIMITED's path U10.6 → U11.7 52.62 → 52.66 mΩ (0.1 mm solve; the wedge's copper had widened the path into C98.1, Inference; 26 mV at 0.5 A either way). C21 is removed from the list |
| R8P4-PLANES-01 | Minor | — | worth fixing (records) | The scorecard records not fully moved to fix pass 3: C4 still 1752.5 mm; the value column headed "R8 (fix pass 2)"; the P1 / P6 moves credited to D106 / D107's B.Cu edits, which change no In1 / In2 fill (they come from D108's via: In1 GND antipad 0.958 → 0.791 mm², In2 BAT_IN perimeter −0.3 mm); P3b's via cluster "under U4's pads" (it lies aft of them, y 55.65–56.35 against pads ending at y 55.05) | **Fixed (records):** C4 "1752.2 mm … (fix pass 2 1752.5; D108's 0.5 mm BAT_ENABLE via −0.3 mm)"; the header "R8 (fix pass 3)"; the attribution (S rows D106 / D107; P1, P6 D108); P3b "beside U4's aft pad row" |
| R8P4-DFM-01 | Minor | — | worth fixing (records) | The fix-pass-3 records called R172 an 0603 (it is `rocket:R0402`) and justified not re-running the plate model on a wrong premise: the model carries every part as a model-box-volume mass; R172's 0.5 mg moved 0.05 mm is what makes it immaterial | **Fixed (records):** the requalification paragraph ("an 0402"), the vibration row (C83 and R81 0603s, R172 0402; re-run by pass 3 DFM on `990c8040…` and pass 4 DFM on `c84f00b8…`, every value equal to `plate_r8.json` but the board SHA), `fix3_handoff.md`. `plate_r8.json` not regenerated (optional; the same values) |
| R8P4-DFM-02 | Minor | — | not worth fixing | The fix-pass-3 rebuild re-placed R70's designator by (+0.104, −0.173) mm, so the bottom silkscreen Gerber changed as well as R172's CPL row, unrecorded | **Fixed (records, fix pass 4):** the fix-pass-3 records now name it: R70's designator was re-placed by `r8_post.py` (0.2 mm), bottom silkscreen only (`fix3_handoff.md` "What changed", M3_R8 "R8 manufacturing outputs", this record's fab row); ink 0.175 mm from R70's courtyard (was 0.003) and 0.376 mm from C70's (was 0.549), still nearer its own part, every silkscreen gate holds. Fix pass 4's rebuild changed no silkscreen item (571 of 571 equal to `c84f00b8…`; R70's reference still (29.228, 31.621)) |
| R8P4-INTEGRITY-01 | Minor | — | worth fixing (owner action) | R8 still uncommitted at pass 4 (89 paths: 38 modified, 51 untracked); the full reviewed pass-3 state survives only in the session scratchpad backup `r8_backup_990c8040/`, and `c84f00b8…`'s state only in this worktree | **Not done: owner action** (no commit allowed in this pass): commit or tag `m3-assy-r8` at this state (`git add -A`), record the commit beside `c84f00b8…` here and in STATUS, and have any further fix pass diff against it. The records pass left the board and every build output unchanged, so a commit now holds the reviewed board |
| R8P4-INTEGRITY-02 | Minor | — | not worth fixing on its own | `r8_build.sh` l. 30–31 describes `r8_ground.py` as drawing "six pour trims"; there are seven since fix pass 1 (G7, D90; the build prints "7 pour trims") | **Fixed (fix pass 4):** `r8_build.sh`'s stage note now reads "seven pour trims (D65, D90)" (a comment: no build output depends on it) |

## Review pass 5 (board `cc044ea0…`) and its records pass

Three independent reviewers re-checked fix pass 4's board `cc044ea0…` in a focused confirming pass: build integrity,
planes and return paths, and routing simplicity (`sources/r8_review/pass5_integrity.md`, `pass5_planes.md`,
`pass5_routing.md`). The other five dimensions (pyro and arming, requirements, RF, power / thermal, DFM / fit) were not
re-run on `cc044ea0…`; fix pass 4's evidence re-ran their measurements on it (requalify, pyro neighbours, DC solves,
reference audit, binding note). Each reviewer found the board's SHA-256 and `git status` (89 paths) the same before and
after its review, and wrote only its report. Result: **0 Critical, 0 Major, 3 Minor** (integrity 2, planes 1, routing 0),
so no finding needed the three-skeptic check ("—" below). Passes 2–5 found no Critical or Major.

- **Gate and reproduction:** `tools/check.sh` exit 0 (all three). From a fresh clone of 431025d plus the worktree,
  `r8_build.sh` reproduces all 1351 files byte for byte; the step-7 table regenerates byte for byte from the real step-6
  board and with `--built`; the fab package regenerates (BOM, CPL and the cost and stock reports byte-identical; the
  Gerbers, job file and PDFs differ only in their dates and PDF IDs, the manifest only in those outputs' hashes); every
  `fix4_*` evidence file regenerates, the scorecard row for row; 272
  tests in 17 suites and quality_audit 21 OK. The 12 rigid digests equal R7's.
- **Fix pass 4's diff against `c84f00b8…`** (rebuilt from 431025d and the coordinator's backup; all 276 baseline hashes
  verify): exactly D110 / D111's copper (13 segments out, 12 in), the three GND vias moved 0.05 mm, and the fills that
  follow from them: F.Cu GND +0.236 mm², B.Cu GND +0.876 mm², and the In2 3V3 pour's clearance ring round the moved
  stitch via (22.05, 26.7), area unchanged. Footprints, zone outlines and settings, graphics, text and setup are equal; no
  gate, test, allowlist, threshold or exemption file changed since pass 4; no code keys on a board SHA. Seeded defects at
  fix pass 4's moved vias and lanes fire `check_r8`'s fence check, the step-7 table gate and the `strip_gnd` digest.
- **Planes:** no regression. Every critical reference, split crossing, critical-via partner, In1 hole, island via count,
  finger list and GND-pad reach equals pass 4's; every P row is equal. The F.Cu GND strip between RADIO_MISO_MCU and
  RADIO_MOSI widens 0.495 → 0.595 mm, and the B.Cu sub-0.5 mm piece at the old R87.1 branch is gone (local worst GND
  reach 5.58 → 5.09 mm).
- **Routing:** both pass-4 routing findings closed as trialled; no scan category gained an instance; the remaining
  exceptions are those pass 4 dispositioned, and the reviewer's searches found no DRC-clean edit that removes any. No
  finding.

**The records pass after it** (no copper, schematic, placement or build-output change; no D-number) applied the record
corrections below. Files changed: this record (the header, the commit paragraph, the step table, the hard-gate row, the
scorecard intro, the review-history row, this section, the owner summary, "Open after fix pass 4"), M3_R8, STATUS,
README, ORDERING (the opening status sentence), `sources/r8_review/fix4_handoff.md` (its scorecard paragraph) and
`fix4_progress.md` (build 1's zone note). After it `tools/check.sh` exits 0, and every other file in the worktree, board
`cc044ea0…` included, is byte-identical to before it (SHA-256 of each checked). AGENTS.md was not edited: its §1
manufacturing row still says the fix-pass-4 board "has not itself been reviewed" and needs the same review-status
sentence.

| ID | Sev. | Skeptics | Reviewer's call | Finding (short) | Disposition |
|---|---|---|---|---|---|
| R8P5-PLANES-01 | Minor | — | not worth fixing on its own (records) | The scorecard intro said fix pass 4 moved "no P, R or D row", but R7 (extended reference samples) moved 102,384 → 102,408, as the same paragraph said a few lines later; `fix4_handoff.md` l. 57 repeated it ("Every P, R and D row equal") | **Fixed (records):** the intro now reads "no P or D row moved, and of the R rows only R7's sample count (+24 on RADIO_MISO_MCU's longer lane, none unreferenced)", and so does `fix4_handoff.md`'s scorecard paragraph. No board effect: every P row, R1–R6b, R8 and every D row is equal |
| R8P5-INTEGRITY-01 | Minor | — | worth fixing (owner action) | R8 still uncommitted at pass 5 (89 paths: 38 modified, 51 untracked); the reviewed pass-4 state `c84f00b8…` survives only as the coordinator's scratchpad backup `r8_backup_c84f00b8/` (pass 5 verified that it rebuilds `c84f00b8…` and all 276 baseline hashes), and `cc044ea0…`, the state pass 5 reviewed, only in this worktree | **Not done: owner action** (no commit allowed in this pass): commit or tag `m3-assy-r8` at this state (`git add -A`; nothing R8 needs is gitignored), record the commit beside `cc044ea0…` here and in STATUS, and have any further fix pass diff against it. The records pass left the board and every build output unchanged, so a commit now holds the board pass 5 reviewed |
| R8P5-INTEGRITY-02 | Minor | — | not worth fixing on its own | Fix pass 4's notes gave the zone changes as F / B GND only (`fix4_progress.md` l. 32); the In2 3V3 pour's clearance ring round the moved stitch via also moved 0.05 mm west, (22.10, 26.70) → (22.05, 26.70): 0.050 mm² removed at x 21.55–22.03 and the same added at x 22.12–22.60, y 26.20–27.20, the pour's 1513.828 mm² unchanged. The necessary consequence of moving a through via, not a forbidden change; only the description was incomplete | **Fixed (records):** `fix4_progress.md`'s build-1 diff line adds "and the In2 3V3 antipad round (22.05, 26.7), area unchanged"; the scorecard intro names it. No function effect (DRC 0; P6 1752.2 mm equal) |

**Notes from the pass (no finding; only the last one changed a record):**
- C19's `width_change_junction` reason ("equal widths would put the wide width into a narrow pad (a gated neck-down) or
  narrow the trunk") is loose: route_check gates a neck only more than 1 mm from the pad (`neck_down`'s pad-entry
  exception), and a 0.4 mm drop would fit R87.1's 0.95 × 0.8 mm pad with no neck. The width is set by C19's first reason,
  each width set by its own load (a divider tap). For the next records edit of C19 (pass-5 routing §9).
- The step-7 table regeneration is still a manual step (build to step 6, `make_ground.py`, rebuild); fix pass 4 did it
  correctly, and a stale table would still have to pass every gate. The renders `r8_top.png` / `r8_bottom.png` are not
  byte-reproducible; they are not fab outputs (pass-5 integrity §7).
- The build's fixed KIID seed gave 199 geometry-unchanged items new UUIDs in fix pass 4: no plane, fabrication or gate
  effect (pass-5 planes §9). The MISO–MOSI F.Cu GND strip (0.595 × 7.7 mm, stitched twice, its tip 3.5 mm from the
  nearer via) acts as a guard between the two lanes (Inference); no action.
- The commit paragraph's "neither fix-pass brief allowed one" was stale after four fix passes (pass-5 integrity §7):
  corrected in this records pass.

## R8 deviations for owner acceptance

### Owner summary (board `cc044ea0…`, fix pass 4; review pass 5 re-checked it in three dimensions)

**Owner acceptance (2026-10-20):** the owner accepted this list as recorded for board `cc044ea0…`, including the C10 vibration
item and the listed agent decisions; with it, REQUIREMENTS M2 is met for R8 in CAD. (Before acceptance, M2 counted every
item below as a deviation from the clean-routing criterion.) R7's acceptance (2026-10-18) was for `c872a3d3…` and does not carry
over. Any copper change reopens the list. Review status: passes 2, 3 and 4 found no Critical or Major (pass 4 on fix
pass 3's board `c84f00b8…`: 0 Critical, 0 Major, 16 Minor); fix pass 4 applied pass 4's two copper Minors (D110,
D111), which took C12 #5 / #6 and C21 off this list; review pass 5 re-checked its board `cc044ea0…` in build integrity,
planes and routing (0 Critical, 0 Major, 3 Minor: two record items and the owner's commit, none needing copper), so the
counts below are unchanged (3 allowlist entries, 0 leftovers, 20 review rows, 91 information instances); the other five
dimensions were not re-run on `cc044ea0…` (a further re-check is the owner's call); still open: the owner's acceptance
of this list, U4 consigned, JLC's tab acceptance and a cost and stock run within 24 h.

**The decision asked:** accept this list for R8, or send the board back for more work first (and, separately, rule on
C10, the vibration item, which is not an M2 item).

| Part | What it holds | Entries | AGENTS §3 | Held by |
|---|---|---:|---:|---|
| A | `route_check` allowlist (gated rules on critical nets) | 3 | 1 (A8) | the gate: matched and re-measured every run |
| B | non-critical leftovers | 0 | 0 | the gate |
| C | review deviations the gate does not hold | 20 rows (C1–C10; since fix pass 1 C11–C18: 23 chain detours, 26 close track / via net pairs (28 before fix pass 4) and, since fix pass 2, 33 close pad / copper pairs (29 listed, 4 fine-pitch own-part escapes counted), 12 nets with vias beyond their need, 26 via folds, 17 narrow F / B GND pieces, 2 solid RF clamp pads, 4 solid THT GND pins, 1 off-axis pad entry; since fix pass 2 C19: the information categories behind C2's miss; since fix pass 3 C20: one footprint silkscreen dot on a foreign pad's mask opening; review pass 4's C21, an acute branch with a doubled same-net run, removed by fix pass 4, D111) | 0 | review (`step9/m2_sweep.py`, part F; review pass 4, re-checked on `cc044ea0…` by review pass 5's routing reviewer) |
| E | information-only `route_check` instances | 8 categories, 91 | 0 | counted, never gated |

R7's list held 45 + 29 entries and 25 rows (299 instances) and 252 information instances. Part F states, for every M2
review category, that it was swept on the final board and what was found.

**Removable or not:** most rows give a measured cause that cannot be removed without a priority-1 cost; these say instead
that they are "not removed yet" (no cheap edit found, none searched exhaustively): C12b #3 (Q123.3 / PULLPIN) and #11 /
#12 (R166 / RAW_PROTECTED; a clean 0.025 mm move exists but gains nothing, the GND pour stays 0.151 mm from R166.1), C11's
four "found" redraws (each found but not simpler) and up to 72 of C19's R8-new information instances (beyond the
one-segment search); C20 is cosmetic (the Gerber is clipped). Fix pass 3 removed three of pass 3's "not removed yet"
rows (C12b #18, #20, #21) and CAM_PWR_EN's hidden redraw (D106–D108). Fix pass 4 removed the two rows review pass 4
found removable and trialled clean: C12 #5 / #6 (R8P4-ROUTING-01, D110: the radio trio's below-fence lanes 0.1 mm west
and three GND vias 0.05 mm west open both pairs to 0.200 mm) and C21 (R8P4-ROUTING-02, D111: a straight T drop, 1.86 mm
shorter, at the cost of one more information instance, C19). No row is now marked removable and not applied.

**Agent decisions in this list that relax a plan gate or an owner criterion** (for the owner to accept with the list):
D5 (loader-driven pins may carry seven reasoned non-LED nets, not LEDs only); D51 (A2 / A3, the GNSS limiter's two
detours, allowlisted as inherent items beyond the plan's TXEN and A8: D11's agreed fallback; R8P3-REQUIREMENTS-03); D10 (M2's detour test judges an MST edge
that crosses a hard keep-out on its shortest path round it; changes one net's verdict, RADIO_TXEN); D12 (the 7.7 A rise
limits, taken on the owner's behalf; stricter than R7's accepted values); D68 (P7 = 1, P9 / P10 floors); D70 (S15: the
rigid 3.4 mm ARM1_SENSE In2 link, exempt by name in `check_r8.RIGID_IN2`; C1); D87 (the rf family budget's worst ratio
1.95 → 2.40 for the limiter's paste-clear vias). D89's J123.2 exception is gone: fix pass 2 relieved the pin (D101).

### A. `route_check` allowlist (3 entries; `tools/route_check.py` profile r8)

| # | Rule | Net, location | Measured reason | Why it stays |
|---|---|---|---|---|
| A1 **§3** | critical_via_no_gnd | PYRO1_GATE via in TP122 (20.45, 92.4), B.Cu | nearest GND via 2.717 mm; a GND via within 1.5 mm would come within 0.45 mm of the bare test pad, which keeps 1.0 mm from foreign copper; `nognd_audit` finds no spot (re-run every check) | inherited with the rigid CH1 block (D9); no current flows through it (TP122 is a probe point, the gate is driven on F.Cu); curing it re-opens the block's R4 spacing and leakage qualification |
| A2 | detour | GNSS_LNA_EN, U30.13 → Q31 / R303 | 7.65 mm against a 3.72 mm octile MST (2.06×, +3.93 mm; R7 7.45 mm; step 9 6.45 mm), 1 via at (11.51, 8.3) | U30_KEEPOUT bars the via under the module and the 1.1 mm pad pitch leaves no spot beside the pad; the module's T-shaped paste extension covers the first 0.6 mm past the pad end, so the via sits at R7's spot, its ring 0.15 mm clear of the aperture (D51, D87; the step-9 spot y 8.9 printed paste over the tented hole) |
| A3 | detour | GNSS_VCC_RF, U30.14 → R300 / Q32 | 6.20 mm against 2.61 mm (2.37×, +3.59 mm; R7 6.2 mm; step 9 5.00 mm), 1 via at (10.41, 8.3) | as A2 (D51, D87) |

### B. Non-critical leftovers

None (`route_check.LEFTOVERS` is empty for R8, and an unrecorded leftover fails the gate).

### C. Review deviations the gate does not hold

| # | Item | Measured | Why it stays (decision) |
|---|---|---|---|
| C1 | S15: In2 signal track | 3.4 mm, ARM1_SENSE at x 14.55, y 94.15–97.55, the rigid CH1 block's internal link | D70: R7's exact segment, exempt by name in check_r8; rerouting it re-opens the block's qualification |
| C2 | P7: an outer GND island with one via | the D4.2 pocket (2.89 mm², via (9.0, 33.8) shared with U10.2), enclosed by the USB flow-through lanes | D63 / D68: a second via would come 0.07 mm from D4.2's pad and 0.15–0.22 mm from USB_DP |
| C3 | P9 / P10: GND-via distance over the board | p95 4.47 / max 9.65 mm against 3.5 / 7 mm (fix pass 1: 4.48 / 9.65) | D64 / D68: floors 4.32 / 9.42 mm under the via rules on this 7.7 A copper; inside the outer GND pours p95 2.90 / max 5.89 mm |
| C4 | P6: In2 perimeter | 1752.2 mm against ≤ 900 mm (R7 1581; step 9 1788.7; fix pass 1 1782.9; fix pass 2 1752.5, cutting the In2 BAT_IN island back, D97; fix pass 3 −0.3 mm by D108's 0.5 mm BAT_ENABLE via, R8P4-PLANES-01) | five regions (target met) whose edges include 294 mm of GND-via antipads (D67); the plan target assumed fewer vias |
| C5 | S8 / S9: nets over 1.6× / 2× their MST | RAW_ACT_SENSE_MCU 2.58 mm against 0.71 mm (3.62×; 1.87 mm excess, under route_check's 2 mm slack; 2.63 / 0.69 mm before fix pass 3 moved R172 0.05 mm east, D106); RADIO_TXEN 2.30× (1.25 on D10's keep-out baseline); GNSS_VCC_RF 2.37× / GNSS_LNA_EN 2.06× (A2, A3; over 2× since their vias moved clear of U30's paste, D87, S9 2 → 4) | RAW_ACT_SENSE_MCU: D33's one inherent VLOGIC crossover at U1's pin 17; TXEN: the U31 body (F10) |
| C6 | R6b: critical-reference share | 0.1107 against ≤ 0.08 (step 9: 0.1157) | D74: own via antipads 69 %, the crystal's In2 keep-out 26 %, other vias' antipads 4 %; 0 samples over another fill, a split or a void |
| C7 | R5 L10 at two MCU-side pyro vias | ARM1_SENSE_MCU (29.3, 47.5): R170 0.635 mm, R172 0.685 mm (0.635 before fix pass 3, D106), C15 0.835 mm; PYRO1_CONT_MCU (24.0, 53.7): R168 0.235 mm (rule 1.0 mm) | D61: tented, on the MCU side of the 4.7 kΩ sense resistors; R7 had the same class closer (0.035–0.185 mm); gated at these figures (`L10_EXCEPT`) |
| C8 | Power layer changes without a GND via within 1.5 mm | 3V3 (29.25, 39.0) 2.40 mm; CAM_IO_3V3 (35.45, 48.5) 2.43; 3V3A (26.5, 54.4) 2.46; VBUS (11.1, 33.8) 1.50; VBUS (7.95, 36.0) 2.06 (since fix pass 1: C83 took the return via's spot, D88; C83 bypasses VBUS to GND 1.8 mm away); CAM_5V (40.75, 41.4) 2.94; VLOGIC (35.65, 66.6) 3.25 mm | no legal spot (step 7's model, `make_ground.py` re-run in fix pass 1); information in route_check (AGENTS §3 asks it of critical signal nets only) |
| C9 | D59: the last links not drawn by r5_maze | nine U9 / U11 local links drawn as polylines, 1.00–1.14× | r5_maze's lattice leaves sub-0.1 mm jogs (an M2 item); the plan's constraint (one layer, no via, ≤ 1.3×) is asserted instead |
| C10 | Vibration (P2; not an M2 item) | f1 209–490 Hz with the plugs on the sled, 6–8 % below R7 (221–533) and 13 % below R6's pinned value | D75: C84 on the mode-1 antinode (−16.6 Hz); inside the 100 g design load (Inference); no sixth support (owner-delegated in R7); moving C84 toward a support gains about 17 Hz at the cost of re-opening the power and routing stages |
| C11 | Chain detours on nets without a pour (M2 "no needless detours"; the gate's detour test works per net): 23 runs, 17 on critical nets, 6 on non-critical (table C11 below) | route_check's own chain test (a run between pads, vias, T nodes or ends > 1.25 × the octilinear distance of its ends and > 0.5 mm longer) and its redraw search `alt_audit` (1–3 segment polylines through RedrawCheck; pads and vias stay put), applied to every net without a pour by `step9/m2_sweep.py`. Pass 1 counted 27 on `429b6db4…`; fix pass 1 removed 4 (VBUS's by C83's move, D88; VLOGIC's sense run, USB_DM out of D4 and ACT_GATE's stub by redraws, D91); fix pass 3 shortened CAM_PWR_EN's by 1.98 mm (D107). Since fix pass 3 `m2_sweep.py margin_free` also runs `alt_audit` at DRC's own threshold (RedrawCheck's 0.01 mm margin hid CAM_PWR_EN's redraw, R8P3-ROUTING-03): it finds only the 4 "found" rows below | 19 have no 1–3 segment redraw (longer redraws, moved pads or vias not searched); 4 have a found redraw that is not simpler (a 0.05 mm segment, an off-grid 0.2 mm segment in the strip, one more bend, and a 0.35 mm segment inside U13.1: built and reverted, D91). Each run's reason is in the table |
| C12 | Edge gaps under 0.2 mm between different nets (adjacency; R7 C15's convention, pads included since fix pass 2, D104): **track / via pairs** 26 net pairs, 7 at the 0.150 mm DRC minimum and 19 at 0.171–0.198 mm (table C12 below; 28 / 9 before fix pass 4, D110); **pad / copper pairs** 33 (pad, net) pairs, of which the 4 fine-pitch own-part escapes are counted (SWDIO past U1.73 / .74 / .75 and CAM_ILIM beside U7.8, both 0.150 mm: a track leaving its own pin beside a neighbour of the same part at 0.5 mm pitch) and the other 29 listed (table C12b). Scope: every track, via and flashed pad of the board on every copper layer | `m2_sweep.py adjacency` (track / via pairs) and `adjacency_pad` (pad against track / via on each layer the pad is flashed on, one row per (pad, foreign net); fix pass 2, R8P2-REQUIREMENTS-01 / R8P2-ROUTING-03: pass 1's sweep compared tracks and vias only). Fix pass 1 opened four 0.150 mm signal pairs (BUZZ_DRV / PULLPIN, I2C1_SCL / SDA, RADIO_NRST / CAM_MCU_RX's via, SERVO1_MCU / VLOGIC's sense via, D91); fix pass 2 four more with the board's 0.5 mm via (CAM_5V / GND, CAM_MCU_TX / GND, RAW_PROTECTED / VLOGIC, GND / RAW_PROTECTED's 0.150 mm, D98) and R81's two BAT_IN pad pairs by moving R81 (D100); fix pass 3 CAM_PWR_EN / USB_LIMITED (0.150 → 0.200 mm) and R172's two pad pairs against USB_LIMITED (0.180 → 0.230 mm) by moving the trunk and R172 0.05 mm (D106), and Q120.9 / BAT_ENABLE's via (0.180 → 0.23 mm) with the board's 0.5 mm signal via (D108); fix pass 4 GND / RADIO_MISO_MCU and GND / RADIO_MOSI (0.150 → 0.200 mm, both against the fence via and the stitch via in the MISO–MOSI slot) by centring the radio trio in its fence opening and moving three GND vias 0.05 mm (D110) | All DRC-legal at the board's 0.15 mm default (REQUIREMENTS "accepted risks"; the pyro rules A–H cover none of these pairs). The remaining 0.150 mm signal pairs are adjacent U1 pins (0.5 mm pitch) escaping to a via beside the neighbour's lane, or a pad-pitch-bound via (U4, U12): not cheap to open (D91; fix pass 3 opened the one TP73-bound pair by moving USB_LIMITED instead, D106). The two strip GND-via pairs in the radio bus's MISO–MOSI slot, which were not pad-bound, were opened by fix pass 4 (R8P4-ROUTING-01, D110). The 0.171–0.198 mm GND pairs are step 7's vias at the rules + 0.02 mm. The pad rows give what a short does; the battery-live and switch-defeating ones are also in the pyro observations. None can fire a channel; since fix pass 3 no listed pair puts 5 V on an MCU pin (R172.2's USB_LIMITED pair, PB0 with no series resistor, is 0.230 mm, D106); JLC's electrical test screens shorts (Inference). The pad rows name the nearest GND track or via; the outer GND pours keep their 0.15 mm zone clearance from bare pads as well (0.151 mm measured at R120.2, C120.2, R121.1 / .2, Q122.3, J1.4, J123.1, R160.1, R165.1), so a GND row is usually no closer than the pour beside the same pad (R8 pass 3, D109) |
| C13 | Vias beyond what a net's pads need (M2 "extra vias"; the gate allows need + 2 on every net, so none fails): non-critical BAT_ENABLE 2 (needs 1), NRST 2 (1), CAM_MCU_RX 2 (0), ACT_GATE 2 (1); critical 3V3A 3 (1), ARM1_SENSE 3 (1), PYRO1_GATE_N 2 (0), RADIO_TXEN 2 (0), RAW_PROTECTED 3 (1), USB_LIMITED 2 (0), VBUS 3 (1), VLOGIC 2 (1) | `route_check --routes` (m2_sweep `routes`) | BAT_ENABLE: R165's via (D30) and the via to the B.Cu spine to U9.1, R81 on a stub since fix pass 2 (D58, D100); NRST: C24's dive under U1 (spike a) and J2.3's edge entry, reachable only from the edge (D53); CAM_MCU_RX: D56's one RX / TX order swap (E short_layer_hop); ACT_GATE: the F.Cu bar over the 7.7 A B.Cu bridge between the facing FETs (D43; In2 carries power only, D20); 3V3A: the F.Cu hop over the pyro corridor (two vias) and U1's VDDA via (D44); ARM1_SENSE: the rigid exit via and the rigid In2 link's two (D70); PYRO1_GATE_N: the rigid exit via and its dive at U1 (D57); RADIO_TXEN: R7's rigid loop (C5, D10); RAW_PROTECTED: U9.6's via, U11's IN1 via and U7's drop (D36, D42, D37); USB_LIMITED: the hop over the RAW_ACT_SENSE lane (D42, E); VBUS: each J3 VBUS pad's via to the B.Cu spine and D4.5's under D4 (D53); VLOGIC: C84's via and the sense via (D33) |
| C14 | Fold-backs through vias (a via whose arms on two layers leave it within 45° of each other; R8P1-ROUTING-04): 26 vias (table C14 below). The deliberate critical-net folds: QSPI_IO3 (27.75, 43.83) 1.15 mm, QSPI_IO2 (17.5, 42.57) 0.60 mm, SPI1_MISO (8.79, 55.75) 1.20 mm, SPI1_MOSI (9.5, 55.65) 0.89 mm; and QSPI_IO3's knee (24.5, 38.45)–(24.0, 38.95), 0.5 mm, held 0.65 mm clear of IO1's via | `m2_sweep.py via_fold` (pass 1 routing's `viaturn.py` method) | QSPI_IO2 / IO3: U3's outer-end via scheme under U1 (spike a); SPI1_MISO / MOSI: U4 fixed at rotation 0 for its axis map (D77), SPI pads facing away from U1, no via under its body (D54); the knee: a straight drop would join the diagonal at exactly the 0.15 mm DRC minimum. The rest are A2 / A3, C5, three rigid R7 vias, T-junctions (HSE_OUT's since D86 at 45° with no plan overlap) or forced entries. HSE_OUT's removable far-side fold is gone (D86); not gated (every remaining critical-net fold is forced) |
| C15 | Unstitched GND pieces 0.5–1.0 mm wide (R7 C11; M2 "unstitched GND pour fingers" beyond the gate's 0.5 mm): by R7's method (relief rings not excluded, F / B) 10 narrower than 0.75 mm and 17 narrower than 1.0 mm (fix pass 1: 11 / 17; pass 1: 12 / 18; R7: 23 / 48); by the gate's method (rings excluded, every layer) 6 / 14 (unchanged). Worst copper distance to a GND via, with the GND pads each piece serves: B.Cu (33.55–40.5, 47.7–53.93) round U13 / C93, 11.1 mm (U13.2 9.28 mm, C93.2 7.24 mm of copper); F.Cu (19.82–43.37, 98.66–99.51), the strip between BAT_ENABLE's and RAW_PROTECTED's lanes that carries Q122's pocket east (Q122.2 12.42, R123.2 12.98 mm: gate charge of Q120 / Q121), 10.3 mm; In1 (0.5–5.88, 91.88–107.74) along the west edge under the RAW_ACT band (no pad), 9.9 mm; the rest ≤ 7.2 mm (J9.2, the camera return, 6.92 mm). U9's island (B.Cu 42.05–45.5, 82.44–87.27; U9.8, R84.2, C81.2) is no longer on the list: fix pass 2's pad stage put a GND via in it, U9.8 now 2.54 mm (D102) | `route_check.pour_pieces` at 0.75 / 1.0 mm by both methods, copper distance by `route_check.reach` to 40 mm on a 0.1 mm raster, GND-pad copper reach at 0.05 mm (fix pass 2, `step9/evidence/fix2_measurements.json`) | Each lies beside a stitched pour (Euclidean cover and P11 met). Searched for a via where an IC GND pad is served (D102's stage): none legal that U13.2's copper reaches; Q122's pocket lies over the B.Cu BAT_IN neck, where D62 forbids antipads (D64's trade); J9.2's pocket is boxed in by CAM_RX_WIRE, J9.1's CAM_5V stub and the RAW_PROTECTED trunk (R8 pass 2 planes: no legal centre). The radio-bus finger (0.54 mm, 15.1 mm) is trimmed (G7, D90). None lies in the RF strip; RF effect negligible (Inference, as R7 judged the class) |
| C16 | D30.2 and D31.2 (the RF ESD clamps' GND pads) solid to the GND pour (R7 C13) | house thermal-relief rule's RF exception (`check_r7.RF_SOLID_GND`) | a spoke adds return inductance at the jack, where the clamp works; rigid strip parts (`strip_parts` digest equal to R7's); the tombstoning risk is caught by ORDERING §5's first-article inspection |
| C17 | Through-hole GND pins with solid zone connections (M2: thermal reliefs where the spokes are not starved): J122.3 / 6 / 9 / 12 (solid on four layers) | KiCad DRC with J122's GND pins given the THT relief on a scratch copy of the final board (fix pass 2): J122.3 resolves 1 spoke on F.Cu (`starved_thermal`), J122.6 / 9 / 12 2 on F.Cu and In2 and 4 on In1 | J122's GND pins carry the 7.7 A servo return (MARGIN_PRESCRIPTION P1-9; the DC_GND solve), J122.3 would be starved on F.Cu, and the pins are in the rigid `j122_tie` digest (D15). J3's legs 1 / 4 (fix pass 1, D89) and J123.2 (fix pass 2, D101: B.Cu 2 spokes, F.Cu and In1 4 on the final copper; fix pass 1's "starved on B.Cu" held only on the step-6 board) have reliefs |
| C18 | C75.1's CAM_5V entry: the 0.8 mm bar from L3.2 runs at x 38.85, 0.35 mm off the pad's axis, and overhangs the pad's inner edge by 0.25 mm (R8P1-ROUTING-02) | pass 1 routing (`padedge.py`, `entry.py`); `m2_sweep.py pad_edge` finds no track end within 0.03 mm of any pad's edge on the final board (pass 1: U9.5, C75.2, U9.7, all fixed, D94) | L3.2 and C75.1 overlap by only 0.3 mm in x; C75 cannot move east (C75.2 against the RAW_PROTECTED trunk at x 42.15) nor L3 west (the camera buck's loop, D41); the joint is continuous copper (D94) |
| C19 | C2: information-only `route_check` instances, 91 against the plan's ≤ 80 (scorecard; R8P2-REQUIREMENTS-04; 90 before fix pass 4's T at R87.1, D111) | per category (part E): pad_end_offcentre 41, width_change_junction 15, passes_through_pad 8, segment_inside_pad 7, u_turn 7, power_via_no_gnd 7, extra_bends 4, short_layer_hop 2. 19 of the 91 lie on copper identical to R7's (the CH1 block, the RF lines, the limiter: 9 pad entries, 3 width steps, 5 pass-throughs, 2 U-turns); 72 are R8-new. Fix pass 2 searched the pad-entry categories (scratch `e_analysis.py`, `step9/evidence/fix2_part_e.json`): for every pad_end_offcentre and segment_inside_pad end, a move of the end to the pad's centre on its own segment's heading, tested with route_check's RedrawCheck | **pad_end_offcentre 41:** no end can reach its pad centre on its own heading: in 39 the centre lies off the segment's octilinear headings (a lateral offset set by the lane pitch against the pad pitch, ≤ 0.475 mm on ≤ 1.4 mm pads, up to 0.85 mm on the 1.5 mm bare test pads TP30 / TP85), in J2.3 J2's footprint key-out starts at x 1.715 (the end stops 0.115 mm short, like the SWD ends), and TP85.1's is a shared corner whose other leg would leave its heading; each needs a jog (itself an M2 item), a moved lane or a moved part: not removed (fix pass 2 cut C83.2's from 2 to 1, D99). **width_change_junction 15:** a narrower branch leaving a wider trunk at a T (since fix pass 4 also R87.1's 0.25 mm drop off the 0.4 mm USB_LIMITED trunk, D111, which replaced an acute branch and a doubled run, review pass 4's C21), each width set by its own load (RAW_PROTECTED's 0.25–0.4 mm taps off the 0.5 mm trunk, 3V3's 0.2 mm FB tap, test-pad and sense stubs; 3 in R7's CH1 copper); a step at a T is allowed by AGENTS §3 / M2, equal widths would put the wide width into a narrow pad (a gated neck-down) or narrow the trunk: stays by construction. **passes_through_pad 8:** a lane through its own net's pad on the way (RF lines through D30.1 / L30.2 / D31.1 and the CH1 block's Q124.2 / R173.1, R7's; BAT_ENABLE through TP84.1 and C87.1, its test pad and filter; CAM_FAULT_N through R76.2, its pull-up): the pass-through is the joint; a stub instead would add a T. Fix pass 2 removed R81.1's (D100). **segment_inside_pad 7:** the inner part of an entry that turns inside its pad (C310.1, U31.15, TP30.1, R110.1, R85.1; D4.6's DM run out of the pad's outer end, since a start at the centre passes D4.5 at 0.04 mm; R303.1, forced: the one-diagonal entry fails DRC, R8 pass 2 routing variant `lim`); fix pass 2 removed C83.2's (D99). **u_turn 7, power_via_no_gnd 7, extra_bends 4, short_layer_hop 2:** the routes of C5 / C11 / C14 (RADIO_TXEN and PYRO1_CONT R7's; 3V3A at U4, SPI1_SCK, USB_DM's inner U, SWDIO and RADIO_NRST round U1's pad corners, each with its D-number in part E), C8's seven power layer changes with no legal GND-via spot, the GNSS fan-out to the fence opening and RAW_PROTECTED's first run (D69), and D56's / D42's hops. A redraw search beyond one segment (moving lanes, vias or parts) was not run: up to 71 R8-new instances are "not removed yet" by that measure, though none is removable by the one-segment search the gate itself uses |
| C20 | Silkscreen on a foreign pad's mask opening (M2: silkscreen never on pads; R8P3-DFM-03) | Q123's library-footprint pin-1 dot (bottom, Ø0.4 mm at (17.0, 64.65), outside Q123's courtyard) overlaps R162.2's B.Mask opening by 0.065 mm (0.012 mm², measured on the final board); R8-new since R162's placement (D57); KiCad 10.0.6's `silk_over_copper` does not report it and the project's silkscreen gates measure text | cosmetic: the Gerber export subtracts the mask (`--subtract-soldermask`, ORDERING §2), so no ink reaches the pad, though the remaining dot butts against R162.2 inside JLC's 0.15 mm pad-to-silk distance (JLC's CAM may trim it); moving R162 at least 0.2 mm aft (the reviewer's fix) re-opens the buzzer group's routing and step 7's vias, so it waits for the next placement change there (R8 pass 3 DFM: not worth fixing alone) |

**C11. Chain detours on nets without a pour** (final board; "none" = no 1–3 segment redraw passes RedrawCheck; E = the
same run is also a part-E instance; rows in the sweep's order, by excess: fix pass 3 renumbered #5–#9):

| # | Net (class) | Layer | Run ends (mm) | Length / octile (mm) | Excess (mm) | Redraw search | Why it stays |
|---|---|---|---|---|---|---|---|
| 1 | RAW_PROTECTED (power) | F.Cu | (18.2, 103.79)–(45.2, 83.7) | 47.09 / 35.32 | 11.77 | none | R122's 0.25 mm gate-drive feed: east past R123 and the BAT_IN via field, aft on y 99.75 and up the east-edge trunk, round the CH1 block and PYRO_BLOCK (D46, D69); E extra_bends |
| 2 | BAT_ENABLE (non-critical) | F.Cu | (16.6, 104.5)–(40.42, 93.5) | 39.31 / 28.38 | 10.94 | none | U9's enable from R165 (D30's via): forward between Q122's pads, east on y 98.45 between the CH1 block and RAW_PROTECTED, aft through TP84.1 and C87.1 (E passes_through_pad) to the via by R81 (D36, D58); crosses PYRO_BLOCK (pyro observations) |
| 3 | RADIO_TXEN (rfif) | B.Cu | (28.59, 7.8)–(31.13, 20.15) | 22.72 / 13.40 | 9.32 | none | R7's rigid loop round U31's west side, pins 9 to 19 (C5, D10: 1.25 × on the keep-out-aware baseline); E u_turn |
| 4 | PYRO1_CONT (pyro) | B.Cu | (28.4, 88.61)–(23.17, 54.6) | 45.43 / 36.18 | 9.26 | none | from the rigid exit via (28.4, 88.61) west into the pyro corridor (x 19.25, nested with GATE_N and ARM1_SENSE over In2's GND notch, D47 / D57) and back east to R168 at U1's forward face |
| 5 | USB_LIMITED (power) | B.Cu | (19.4, 37.3)–(29.95, 54.0) | 27.25 / 21.07 | 6.18 | none | under U1's aft pad row on y 37.3 (y 37.25 until fix pass 3, D106), north on x 29.95 (D42): an L round U1's flash dives |
| 6 | GNSS_TP_MCU (rfif) | F.Cu | (23.5, 37.45)–(9.0, 22.88) | 25.96 / 20.58 | 5.39 | none | the nested GNSS river round the USB block to the fence opening 7.685–9.70 (D51, D67); E extra_bends |
| 7 | GNSS_TXD_MCU (rfif) | F.Cu | (22.5, 37.45)–(7.11, 22.75) | 26.87 / 21.48 | 5.39 | none | as GNSS_TP_MCU, the river's outer lane; E extra_bends |
| 8 | GNSS_RXD (rfif) | F.Cu | (18.8, 29.17)–(8.21, 19.7) | 19.36 / 14.51 | 4.84 | none | from R306 by U1's aft face (F10 5 mm, D17) west to U30.3 through the fence opening, nested with TXD / TP |
| 9 | CAM_PWR_EN (non-critical) | B.Cu | (31.85, 43.0)–(30.775, 27.5) | 20.15 / 15.95 | 4.20 | none | D37's loop round U7's west end on x 28.25, then one 45° run into R74.1's centre; the run at y 36.8 is pinned by TP73's 1.0 mm zone. Fix pass 3 (D107, R8P3-ROUTING-03): it was x 28.0 with an L and a 2.78 mm stub into R74.1, 22.12 mm (excess 6.18 mm); the gate's redraw search could not see the shorter drawing while the y 36.8 leg sat 0.150 mm from USB_LIMITED (RedrawCheck tests at the rule + 0.01 mm) |
| 10 | PULLPIN (non-critical) | F.Cu | (20.5, 52.55)–(14.23, 61.0) | 14.43 / 11.05 | 3.38 | none | forward from U1.8 beside BUZZ_DRV, west across the pyro corridor aft of the 3V3A hop, to its via (D58) |
| 11 | SPI1_SCK (spi) | F.Cu | (15.45, 45.5)–(10.0, 56.35) | 16.39 / 13.11 | 3.28 | none | D54's forced crossing round SPI1_MISO's and SPI1_MOSI's vias to its own below pad 13; E u_turn |
| 12 | 3V3A (power) | B.Cu | (11.21, 53.05)–(9.5, 52.84) | 4.60 / 1.80 | 2.80 | none | U4's 3V3A loop round its GND via (10.5, 52.1) to pad 5: no via under the IMU's body (D44, D54); E u_turn |
| 13 | USB_DM (usb) | F.Cu | (6.88, 32.85)–(6.88, 33.85) | 3.36 / 1.00 | 2.36 | none | J3's B7 → A7 inner U joining the two plug orientations on F.Cu without a via (D53); E u_turn |
| 14 | QSPI_CLK (spi) | F.Cu | (30.55, 46.0)–(27.75, 42.57) | 6.23 / 4.59 | 1.64 | none | from pin 36 down x 29.3, 0.35 mm off the east pad row, to its dive via (spike a) |
| 15 | SERVO1_MCU (non-critical) | B.Cu | (32.6, 79.51)–(35.35, 76.85) | 5.12 / 3.85 | 1.26 | none | the outer servo lane's B.Cu leg from its T-via to D121's pin (the reversal to D121's pin order, D7) |
| 16 | SERVO4_MCU (non-critical) | B.Cu | (32.6, 71.89)–(35.35, 74.55) | 5.12 / 3.85 | 1.26 | none | as SERVO1_MCU |
| 17 | PYRO1_CONT (pyro) | F.Cu | (26.83, 87.9)–(24.6, 87.2) | 3.61 / 2.52 | 1.09 | none | rigid CH1 block copper (D9, D15); E u_turn |
| 18 | CAM_5V (power) | B.Cu | (38.5, 47.4)–(40.8, 49.6) | 4.27 / 3.21 | 1.05 | none | C75.1 → U13's middle (C91 tap) round C75.2's GND via (41.4, 47.8) |
| 19 | CC2 (non-critical) | F.Cu | (6.88, 35.35)–(8.57, 37.2) | 3.54 / 2.55 | 0.99 | none | J3.B5 to R8.1: east then forward past J3's pad row (D53) |
| 20 | RADIO_RXEN (rfif) | F.Cu | (25.8, 7.58)–(27.32, 9.05) | 2.74 / 2.13 | 0.61 | found | round U31's south-west corner through R312.1 into U31.10; the one redraw found has a 0.05 mm segment (route_check micro_segment) |
| 21 | 3V3_GNSS (power) | F.Cu | (13.71, 19.7)–(12.61, 20.75) | 2.15 / 1.53 | 0.61 | found | U30.8 joined to U30.7 at y 20.75 (R7's geometry, D11); the redraw found has a 0.20 mm segment and off-grid points in the strip |
| 22 | USB_DP (usb) | F.Cu | (6.88, 33.35)–(8.4, 34.35) | 2.52 / 1.93 | 0.59 | found | J3's A6 pad tees into B6's lane (D53); the redraw found chamfers the corner into three segments with a 0.505 mm stub into the tee: one more bend, not simpler |
| 23 | CAM_5V (power) | B.Cu | (40.8, 49.6)–(39.5, 50.55) | 2.25 / 1.69 | 0.56 | found | U13.1 entered along its axis to its centre; the redraw found (a 45° chamfer) ends in a 0.35 mm segment inside the pad, 0.35 mm off its centre (built in fix pass 1 and reverted, D91) |

**C12. Different-net edge gaps under 0.2 mm, tracks and vias** (final board, one row per net pair at its smallest gap; fix pass 2 removed CAM_5V / GND, CAM_MCU_TX / GND and RAW_PROTECTED / VLOGIC and opened GND / RAW_PROTECTED to 0.171 mm, D98; fix pass 3 removed CAM_PWR_EN / USB_LIMITED, pass 3's #5, now 0.200 mm, D106, fix pass 4 removed GND / RADIO_MISO_MCU and GND / RADIO_MOSI, pass 4's #5 / #6, now 0.200 mm, D110; each pass renumbered):

| # | Gap (mm) | Layer | Nets | Items | Why it stays (a short would …) |
|---|---:|---|---|---|---|
| 1 | 0.150 | F.Cu | CAM_5V_SENSE / RAW_ACT_SENSE_MCU | track y 46.5; via (31.75, 47.0) | U1 pins 35 / 34: pin 35's lane past pin 34's escape via (C5, D33) (… tie two ADC inputs) |
| 2 | 0.150 | F.Cu, B.Cu | CAM_FAULT_N / CAM_PWR_EN | track y 43.5 and B.Cu x 32.35; via (31.85, 43.0) | U1 pins 41 / 42 to a staggered via pair whose B.Cu lanes run at 0.5 mm pitch, so no GND finger forms (D56, D91) (… tie the eFuse's fault flag to its enable) |
| 3 | 0.150 | F.Cu | CAM_IO_3V3 / CAM_UART_OE | track y 48.5; via (35.45, 48.5) | OE ends on U12.6's line beside U12.7's supply via, 0.5 mm pitch (D55, D56) (… enable the translator) |
| 4 | 0.150 | F.Cu | CAM_MCU_RX / CAM_MCU_TX | track y 45.0; via (31.85, 45.5) | U1 pins 38 / 37: TX's lane past RX's hop via (D56) (… loop the camera UART back) |
| 5 | 0.150 | B.Cu | IMU_CS / SPI1_SCK | track x 10.0; via (10.5, 55.65) | U4's 0.5 mm pad pitch with each via below its pad and none under the body (D54) (… tie SCK to CS) |
| 6 | 0.150 | F.Cu | LED_YEL / USB_FAULT_N | track y 45.0; via (14.0, 44.5) | U1 pins 88 / 87: LED_YEL's lane past USB_FAULT_N's via (D52, D57) (… light the LED on a USB fault) |
| 7 | 0.150 | B.Cu | SPI1_MOSI / SPI1_SCK | track x 10.0; via (9.5, 55.65) | as #5 |
| 8 | 0.171 | all | 3V3 / GND | vias (39.325, 82.0) / (38.925, 81.4) | R89's 3V3 via and a step-7 stitching via at the rules + 0.02 mm (… short 3V3: U2's limit) |
| 9 | 0.171 | all | 3V3A / GND | vias (15.0, 62.2) / (15.4, 62.8) | the 3V3A hop's via and a stitching via (… burn R164) |
| 10 | 0.171 | all | ARM1_SENSE / GND | vias (14.55, 97.55) (rigid) / (13.95, 97.15) | a stitching via by the rigid In2 link's via (… read disarmed with the link in: a ground fire is refused, the safe direction against ignition, but the annunciation is false; the ARM link itself is the physical indicator; R8P3-REQUIREMENTS-04) |
| 11 | 0.171 | all | GND / RADIO_TXEN | vias (28.19, 7.2) / (28.59, 7.8) | R7's strip geometry (D10, D11) (… hold TXEN low) |
| 12 | 0.171 | all | GND / RAW_PROTECTED | vias (42.15, 25.6) (V_U7) / (42.55, 25.0) | the camera feed's drop via and a step-7 stitching via at the rules + 0.02 mm; R72.2's via (41.45, 32.6) is 0.20 mm from the trunk since D98 (… short RAW_PROTECTED: U9's limit) |
| 13 | 0.173 | F.Cu | GND / GNSS_TXD_MCU | track y 28.2; via (8.136, 27.677) | step 7's island via (… hold the GNSS UART low) |
| 14 | 0.175 | B.Cu | CAM_IO_3V3 / GND | track x 39.8; via (40.375, 51.875) | stitching via (… short U13's output: its limit) |
| 15 | 0.175 | F.Cu | GND / GNSS_RESET_N | track y 26.4; via (19.125, 25.875) | stitching via (… hold the GNSS in reset) |
| 16 | 0.175 | F.Cu | GND / GNSS_RXD | track x 8.21; fence via (7.685, 23.3) | the fence via at the lane's opening (D16) |
| 17 | 0.180 | all | BUZZ_OUT / GND | vias (15.0, 67.5) / (15.2, 68.15) | stitching via (… sound the buzzer) |
| 18 | 0.180 | B.Cu | GND / GNSS_ANT_DC | track (11.45, 5.15)–(5.85, 10.75); via (9.025, 8.325) | the rigid strip GND via beside the limiter's ANT_DC run (D11) (… the limiter holds the current) |
| 19 | 0.180 | F.Cu | GND / LOGIC_SOURCE_ST | diagonal (34.0, 51.5)–(38.6, 56.1); via (34.625, 52.875) | stitching via (… read the source as USB) |
| 20 | 0.180 | F.Cu | GND / RADIO_RXEN | track y 7.58; via (22.0, 7.0) | the rigid strip GND via (… hold RXEN low, its reset state) |
| 21 | 0.180 | F.Cu | SWDIO / USB_DP | SWDIO diagonal; DP y 36.02 | U1's aft-face lanes at 0.38 mm pitch (D53) |
| 22 | 0.180 | F.Cu | USB_DM / USB_DP | DM's 45° run (D91); DP y 36.02 | the USB pair's pitch (D53) |
| 23 | 0.190 | F.Cu | USB_DM / VBUS_SENSE | DM y 35.64; via (16.6, 35.1) | VBUS_SENSE's drop via under DM's lane (D53) |
| 24 | 0.195 | all | GND / VLOGIC | vias (26.95, 60.5) / (26.6, 61.1) | the sense via and step 7's return via |
| 25 | 0.198 | B.Cu | BAT_ILIM / GND | track (43.0, 86.925)–(43.8, 87.725); via (42.9, 87.6) | stitching via (… set U9's current limit to its minimum) |
| 26 | 0.198 | all | GND / PULLPIN | vias (14.23, 61.0) / (13.6, 61.3) | stitching via (… read the pull-pin as pulled) |

**C12b. Pad-to-copper gaps under 0.2 mm** (final board, `m2_sweep.py adjacency_pad`, one row per (pad, foreign net); the 4 fine-pitch own-part rows are counted in C12; "own part": the foreign net also has a pad on that part; R7: the same pair on R7's copper; every pad bare except U5's):

| # | Gap (mm) | Layer | Pad (net) | Copper (net) | Why it stays | A short would … |
|---|---:|---|---|---|---|---|
| 1 | 0.152 | F | R130.2 (GND) | PYRO1_CONT track y 88.42 | R7's rigid CH1 copper (own part: R130 is CONT's divider bottom); R7 the same | ground the continuity sense: it reads open (no fire) |
| 2 | 0.155 | F | R305.2 (GNSS_TXD_MCU) | GND fence via (7.685, 23.3) | the fence via at the GNSS lanes' opening (D16) | hold the GNSS UART line low |
| 3 | 0.170 | B | Q123.3 (BUZZ_OUT) | PULLPIN lane x 14.23 | R8 lane: PULLPIN's column to R161.2 / D122.3 passes the buzzer FET's drain (D58); not removed yet: x 14.23 is pinned by R161.2, PULLPIN's via (0.198 mm from a GND via) and J123.2's relief, and a Q123 shift needs its BUZZ_OUT / BUZZ_G stubs redrawn (R8 pass 3 routing: not cheap) | PULLPIN follows the buzzer drain: a false or toggling pull-pin witness (advisory only, F9 / FMEA F-7: it can upset the ground PAD_ARMED → READY gate or raise a fault code, never a launch detect; ignored after launch; R8P4-REQUIREMENTS-02) (Inference); no fire path |
| 4 | 0.170 | F | R129.1 (PYRO1_CONT_MID) | GND via (28.55, 87.21) | R7 C15 #1 (0.170 on R7): R7's GND partner of the CONT exit via, redrawn at R7's spot (`r8_route_pyro`) | pass about 1.6 mA through an armed igniter via R173 (R7 C15's figure, far below the 0.30 A no-fire) |
| 5 | 0.171 | B | R162.1 (BUZZ_DRV) | GND via (15.4, 62.8) | step 7's via at the rules + 0.02 mm (D62) | hold the buzzer off |
| 6 | 0.172 | F | FB30.2 (3V3_GNSS) | 3V3 via (12.33, 24.4) | own part: FB30's own 3V3 feed via beside its other pad | bypass the GNSS supply's ferrite |
| 7 | 0.175 | B | C82.1 (RAW_PROTECTED) | GND via (40.875, 76.625) | own part: step 7's via beside C82's GND pad | short RAW_PROTECTED: U9 limits, the logic browns out |
| 8 | 0.175 | F | C84.1 (VLOGIC) | GND via (38.375, 68.375) | own part: step 7's via by C84's GND pad | short VLOGIC: the board browns out |
| 9 | 0.175 | F | LS120.2 (BUZZ_OUT) | GND via (15.2, 70.9) | step 7 | sound the buzzer |
| 10 | 0.175 | B | Q30.2 (GNSS_ANT_SRC) | GND via (3.0, 13.0) | R7's rigid strip copper (D11, D15) | put R300's 15 Ω across U30's VCC_RF (antenna bias lost, Inference) |
| 11 | 0.175 | F | R166.1 (BAT_DAMP) | RAW_PROTECTED track y 99.75 | R8 lane: R122's 0.25 mm gate-drive feed passes the damper (D46, D69); R8 pass 3 routing's variant (R166 0.025 mm aft) is clean and opens both rows to 0.200 mm, but R166.1 keeps the GND pour at 0.151 mm and the lane runs along the GND strip, so the consequence class is unchanged: not applied | load RAW_PROTECTED through R166's 0.33 Ω: U9 limits, the logic browns out |
| 12 | 0.175 | F | R166.2 (GND) | RAW_PROTECTED track y 99.75 | as above | short RAW_PROTECTED: U9 limits |
| 13 | 0.175 | B | R83.1 (BAT_OVLO) | GND via (39.0, 87.7) | own part: step 7's via by R83's GND pad | hold OVLO low: U9's overvoltage lockout lost (D8 still clamps) |
| 14 | 0.175 | B | R84.1 (BAT_ILIM) | GND via (42.9, 87.6) | own part: C88's return via (step 7) | short U9's ILIM resistor (as C12 #25) |
| 15 | 0.175 | B | U5.3 (GND) | 3V3A track y 57.85 | own part: the sensors' 3V3A trunk under U5 past its GND pins (mask-defined pads) | burn R164 (3V3A's filter resistor) |
| 16 | 0.175 | B | U5.4 (GND) | 3V3A track y 57.85 | as above | as above |
| 17 | 0.180 | B | C13.1 (3V3) | GND via (14.8, 51.6) | own part: C13's GND via (spike a) | short 3V3: U2 limits |
| 18 | 0.180 | B | **R120.2 (ACT_GATE)** | **GND via (15.0, 107.3)** | step 7's tented via at the rules + 0.02 mm, not ACT_GATE's nearest GND copper: the masked GND pours stand at the board's 0.15 mm zone clearance from all five bare ACT_GATE / ACT_DRV pads (0.151 mm: B.Cu R120.2, C120.2; F.Cu R121.1, R121.2, Q122.3), as on R7 (Q121.4, R121.1 / .2, Q122.3, 0.150 mm), so moving the via would gain nothing; REQUIREMENTS' accepted gate-net spacing outside the pyro block (D109; R8 pass 3) | turn the actuator switch on with the power switch open (rule H's reason, M3_R4): RAW_ACT live, no fire alone (pyro observations; screened by ORDERING §5's 20 power-switch cycles with RAW_ACT below 1 V between them, and its hot RAW_ACT check) |
| 19 | 0.180 | B | R301.2 (GNSS_ANT_GATE) | GND via (6.0, 15.0) | R7's rigid strip copper | hold Q30's gate at GND: the antenna current limit is lost (as C304's note, ORDERING §4) |
| 20 | 0.180 | B | R302.2 (GNSS_ANT_PD) | GND via (8.0, 15.0) | R7's rigid strip copper | hold the antenna bias on (LNA_EN cannot switch it off) |
| 21 | 0.182 | F | LED2.1 (LED_YEL_A) | GND via (8.125, 42.875) | own part: LED2's GND via | keep the yellow LED off |
| 22 | 0.183 | F | R11.2 (3V3) | GND via (10.6, 57.0) | step 7 | short 3V3: U2 limits |
| 23 | 0.189 | F | J1.4 (BAT_SW_RETURN) | GND via (14.7, 112.0) | own part (J1.2 is GND): step 7; not the nearest GND copper: the pour is 0.151 mm from J1.4 on F.Cu and B.Cu (R7 B.Cu 0.151 mm; D109) | ground the switch's return: the board cannot turn on (fail-off) |
| 24 | 0.190 | B | **Q120.8 (BAT_IN)** | **GND via (19.6, 104.4)** | the band's GND via (spike c, D31; trim G4 round its ring) | short the pack through board copper (the external 15 A fuse clears it) |
| 25 | 0.190 | F | R178.1 (PYRO1_CONT) | GND via (28.55, 87.21) | own part; R7's partner via (as #4) | ground the continuity sense: reads open |
| 26 | 0.193 | B | Q32.3 (GNSS_ANT_GATE) | GND via (8.0, 15.0) | R7's rigid strip copper | as #19 |
| 27 | 0.193 | F | R129.1 (PYRO1_CONT_MID) | PYRO1_CONT via (28.4, 88.61) | R7 C15 #6 (0.193 on R7): the rigid exit via | bypass R129: the continuity reading shifts; no fire |
| 28 | 0.196 | F | C300.1 (3V3_GNSS) | GND fence via (12.3, 23.3) | own part: the fence row (D16) | short 3V3_GNSS: FB30 / U2 limit |
| 29 | 0.197 | F | FB30.2 (3V3_GNSS) | GND fence via (12.3, 23.3) | the fence row | as #28 |

Two pairs left C12b in fix pass 2: R81.2 (GND) and R81.1 (BAT_ENABLE) against the BAT_IN feed x 41.25 (0.170 / 0.180 mm; D100). Three left in fix pass 3 (pass 3's numbering): #18 Q120.9 (BAT_IN) / R165's BAT_ENABLE via, 0.180 → 0.23 mm with the 0.5 mm signal via (D108), and #20 / #21 R172.1 / R172.2 against USB_LIMITED, 0.180 → 0.230 mm (D106); the rows after them are renumbered. J123.1 (PULLPIN_EXT) has a GND via at exactly 0.200 mm ((10.05, 75.3), not listed) and the pour at 0.151 mm on both faces. Of note above 0.2 mm (R8 pass 2 pyro): ACT_GATE's chamfered B.Cu stub 0.264 mm from bare C120.1 (ACT_FET_S; a bridge holds the switch off, the safe direction; C120's own pads sit 0.50 mm apart by design).

**C14. Fold-backs through vias** (final board; unchanged by fix passes 2–4, the same 26 vias and arms):

| Via | Net (class) | Arms (layer, mm) | Angle | Fold (mm) | Why it stays |
|---|---|---|---:|---:|---|
| (11.51, 8.3) | GNSS_LNA_EN (rfif) | F.Cu 1.9 / B.Cu 3.36 | 0° | 1.90 | A2 (D51, D87): the via beyond the pad end and its paste |
| (32.6, 76.97) | SERVO2_MCU (actuator) | F.Cu 2.2 / B.Cu 1.2 | 0° | 1.20 | as SERVO1_MCU |
| (32.6, 74.43) | SERVO3_MCU (actuator) | F.Cu 2.2 / B.Cu 1.2 | 0° | 1.20 | as SERVO1_MCU |
| (32.6, 79.51) | SERVO1_MCU (actuator) | F.Cu 2.2 / B.Cu 1.2 | 0° | 1.20 | T-junction: the via feeds the 1 k (B.Cu) and D121; the F.Cu passes over the 1 k after the pull-down (D7) |
| (32.6, 71.89) | SERVO4_MCU (actuator) | F.Cu 2.2 / B.Cu 1.2 | 0° | 1.20 | as SERVO1_MCU |
| (8.79, 55.75) | SPI1_MISO (spi) | F.Cu 4.09 / B.Cu 1.2 | 0° | 1.20 | U4 fixed at rotation 0 (axis map, D77), its SPI pads facing away from U1; no via under its body (D54) |
| (27.75, 43.83) | QSPI_IO3 (spi) | F.Cu 5.303 / B.Cu 1.62 | 45° | 1.15 | U3's outer-end via scheme under U1 (spike a): the F.Cu crosses the flash diagonally, the B.Cu returns along the pad row |
| (35.25, 60.5) | RAW_PROTECTED (power) | F.Cu 2.1 / B.Cu 1.1 | 0° | 1.10 | T between U11.2 (IN1) and C97.1 (D42, D46) |
| (40.75, 41.4) | CAM_5V (power) | F.Cu 0.925 / B.Cu 1.77 | 0° | 0.93 | T: the sense joins at J9.1's feed via (D41) |
| (9.5, 55.65) | SPI1_MOSI (spi) | F.Cu 4.05 / B.Cu 0.89 | 0° | 0.89 | as SPI1_MISO |
| (13.48, 98.95) | ACT_GATE (actuator) | F.Cu 1.9 / B.Cu 0.87 | 0° | 0.87 | Q120.4 (B.Cu) under the R121 / TP121 column (F.Cu): the bar over the 7.7 A bridge (D43) |
| (10.41, 8.3) | GNSS_VCC_RF (rfif) | F.Cu 1.9 / B.Cu 1.181 | 45° | 0.83 | A3 (D51, D87) |
| (34.4, 73.2) | 3V3 (power) | F.Cu 1.131 / B.Cu 1.35 | 45° | 0.80 | T to D121.5; the In2 tap into the F.Cu hop over SERVO4_MCU (D40, spike b) |
| (0.8, 42.75) | NRST (other) | F.Cu 0.8 / B.Cu 6.1 | 0° | 0.80 | J2.3 reachable only from the board edge (D53) |
| (34.4, 69.65) | 3V3 (power) | F.Cu 3.55 / B.Cu 1.061 | 45° | 0.75 | the In2 3V3 region's only feed from U2 / L1's output line (B.Cu y 70.4; a recorded single point, M3_R8 Power) and the start of the F.Cu spine to D121.5's via (D40); corrected in fix pass 2 (R8P2-POWER-05) |
| (28.4, 88.61) | PYRO1_CONT (pyro) | F.Cu 0.75 / B.Cu 1.428 | 0° | 0.75 | rigid R7 exit via (D9, D15) |
| (35.65, 66.6) | VLOGIC (power) | F.Cu 0.75 / B.Cu 1.1 | 0° | 0.75 | T for C84.1 (F.Cu) and U2.2 / TP83 (B.Cu) |
| (11.45, 5.15) | GNSS_ANT_DC (rfif) | F.Cu 1.03 / B.Cu 7.92 | 45° | 0.73 | rigid R7 via (D11) |
| (24.0, 51.1) | NRST (other) | F.Cu 0.707 / B.Cu 1.202 | 0° | 0.71 | T with C24 (spike a), 0.65 mm off HSE_OUT's lane |
| (24.69, 47.5) | HSE_OUT (crystal) | F.Cu 2.39 / B.Cu 0.99 | 45° | 0.70 | T between Y1.3 and C26.1 since D86: the F.Cu arm and the B.Cu arm to Y1.3 leave 45° apart, no plan overlap (the far-side fold of 0.95 mm overlap is gone) |
| (31.75, 47.0) | RAW_ACT_SENSE_MCU (other) | F.Cu 1.2 / B.Cu 0.948 | 45° | 0.67 | C5: R172 under U1's east pad row (D33) |
| (17.5, 42.57) | QSPI_IO2 (spi) | F.Cu 0.849 / B.Cu 1.57 | 45° | 0.60 | as QSPI_IO3 |
| (8.72, 62.85) | I2C1_SCL (other) | F.Cu 4.639 / B.Cu 0.825 | 45° | 0.58 | T with R12 (pull-up) and U5.8 |
| (9.97, 62.85) | I2C1_SDA (other) | F.Cu 3.578 / B.Cu 0.825 | 45° | 0.58 | T with R13 and U5.7 |
| (23.0, 88.33) | PYRO1_GATE_N (pyro) | F.Cu 0.707 / B.Cu 3.7 | 45° | 0.50 | rigid R7 exit via (D9, D15) |
| (38.25, 33.1) | CAM_FB (other) | F.Cu 0.425 / B.Cu 1.061 | 45° | 0.30 | T (R72 / R71 / C77, D41) |

### E. Information-only `route_check` instances (91; counted, never gated)

Each category's measured reason and what fix pass 2's search found: C19.

| Category | Count | What it is on R8 |
|---|---:|---|
| pad_end_offcentre | 41 | a track ends inside its pad but off the centre, by up to 0.85 mm (TP30's and TP85's 1.5 mm test pads; elsewhere ≤ 0.475 mm, mostly power and long pads). Fix pass 1: U10.2's 0.5 mm went with C83's move; fix pass 2: C83.2's two 0.2475 mm ends became one 0.175 mm end (U10.2's GND on its row into C83.2, the link to the via from C83.2's centre, D99). U9.7's end lies in its inner rectangle 0.05 mm from that rectangle's centre, 0.215 mm from the outer rectangle's centre that this tool measures (D94). The category tests pads up to 2 mm; larger pads are swept by `m2_sweep.py pad_edge` (part F) |
| width_change_junction | 15 | a width step at a junction: RAW_PROTECTED's branches (5), USB_LIMITED's TP82 and R87.1 taps (2; R87.1's since fix pass 4, D111), and one each on 3V3, GND, PYRO1_OUT, PYRO1_BUS, 3V3A, BAT_IN, CAM_5V, CAM_INPUT_LIMITED (a narrow branch leaving a wide trunk); VBUS's went with C83's old feed (D88) |
| passes_through_pad | 8 | a track crosses a same-net pad: the rigid RF lines through D30.1 / L30.2 / D31.1 (R7's copper), the rigid CH1 copper at Q124.2 and R173.1, BAT_ENABLE through TP84.1 / C87.1, CAM_FAULT_N through R76.2; BAT_ENABLE's pass through R81.1 went with R81's move (D100) |
| segment_inside_pad | 7 | a short segment lies inside its own pad (0.22–0.85 mm), at C310.1, U31.15, TP30.1, R110.1, D4.6, R303.1, R85.1 (C83.2's went, D99) |
| u_turn | 7 | a route that turns back on itself (D10-style module and corridor loops): RADIO_NRST, RADIO_TXEN (U31 body), SWDIO, SPI1_SCK, PYRO1_CONT (3.6 mm), 3V3A (4.6 mm), USB_DM (3.4 mm) |
| power_via_no_gnd | 7 | C8 above |
| extra_bends | 4 | GNSS_TP_MCU, GNSS_RESET_N, GNSS_TXD_MCU (the GNSS fan-out to the fence opening), RAW_PROTECTED's first run (D69) |
| short_layer_hop | 2 | CAM_MCU_RX 2.67 mm on B.Cu (the camera UART's RX / TX order swap, D56); USB_LIMITED 1.84 mm on F.Cu over the RAW_ACT_SENSE lane (D42) |

### F. M2 review coverage (swept on the final board)

Every category of REQUIREMENTS M2's "What review checks" was swept on the final board by
`sources/r8_design/step9/m2_sweep.py` (output `step9/evidence/fix4_m2_sweep.json`, on `cc044ea0…`; re-run it after any copper change):

| M2 review category | Swept with | Result | Where |
|---|---|---|---|
| Whole-run (chain) detours on nets without a pour | route_check's chain test + `alt_audit` on every net without a pour | 23 found (17 critical, 6 non-critical) | C11 |
| Detours on non-critical nets (net level) | `route_check --routes` | gated at 1.6 × / 2 mm on every net (LEFTOVERS empty): 0 over; below it RAW_ACT_SENSE_MCU 3.62 (C5; 3.80 before D106), CAM_PWR_EN 1.38 (1.50 before D107), CC2 1.39, CAM_FB 1.31, ACT_GATE 1.21, BAT_ENABLE 1.16 (1.15 before D100), NRST 1.10 (each a C11 run, C5, or a short pad-to-pad L: CAM_FB, a T round R72 / R71 / C77, D41) | C11, C13 |
| Extra vias (non-critical and critical, within the gate's need + 2) | `route_check --routes` | 12 nets over their need, none over need + 2 | C13 |
| Local bumps on non-critical nets | `route_check --bumps-all` | 1 candidate in 7 windows: BAT_ENABLE F.Cu (17.4, 98.45) → (40.42, 93.5), a false positive (its x 42.9 leg passes through TP84.1 and C87.1, BAT_ENABLE's own pads, which the redraw would leave unconnected) | — |
| Bumps and redraws hidden by the search's margin (R8P3-ROUTING-03) | `m2_sweep.py margin_free`: `bump_audit` on every net and `alt_audit` on every C11 run with RedrawCheck at DRC's own threshold (rule − 0.0005 mm instead of rule + 0.01 mm; fix pass 3, D107) | 29 windows: 1 bump candidate, BAT_ENABLE's false positive above; 4 redraws, C11's own "found" rows #20–#23. On `990c8040…` the same search found CAM_PWR_EN's 1.98 mm shorter drawing (now built, D107) and a USB_LIMITED corner chamfer 0.151 mm from a 3V3 via (not clean); neither remains | C11 |
| Layer hops on poured nets whose vias join the pour or are junctions | via-to-via tracks < 4 mm on poured nets | 2: 3V3 F.Cu (34.4, 69.65)–(34.4, 73.2), 3.55 mm, the In2 3V3 tap into the F.Cu hop over SERVO4_MCU's B.Cu (D40); GND F.Cu (24.55–25.45, 89.275), 0.9 mm, rigid CH1 block copper (D9) | — |
| Short layer hops on every net | route_check `short_layer_hop` | 2 (CAM_MCU_RX, USB_LIMITED) | E |
| Steps inside a via's copper | tracks with both ends in one same-net via ring | 1: ARM1_SENSE F.Cu at (18.18, 91.3), 0.2 mm, rigid R7 copper (D9) | — |
| Hygiene on non-critical nets | the gate (LEFTOVERS empty: every instance fails) | 0 | B |
| Pad-entry tidiness | route_check `pad_end_offcentre` / `segment_inside_pad` / `passes_through_pad` (pads ≤ 2 mm) and `m2_sweep.py pad_edge` (track ends within 0.03 mm of any pad's edge, any size) | 41 / 7 / 8 (E, C19); pad edge: none | E, C18, C19 |
| Adjacency on every net | different-net track / via pairs on one layer, edge to edge (`adjacency`), and every flashed pad against every different-net track or via on its layer (`adjacency_pad`, since fix pass 2, D104) | 26 track / via net pairs under 0.2 mm (7 at 0.150 mm; 28 / 9 before fix pass 4, D110); 33 pad / copper pairs (4 fine-pitch own-part escapes counted, 29 listed) | C12, C12b |
| Fold-backs through vias (pass-1 review addition) | `m2_sweep.py via_fold` | 26 | C14 |
| Unstitched GND fingers 0.5–1.0 mm (beyond the gate's 0.5 mm) | `route_check.pour_pieces` at 0.75 / 1.0 mm; GND-pad copper reach | 10 / 17 (R7's method, F / B); IC GND pads within 4 mm of copper of a GND via where a legal spot exists (D102; U13.2 none) | C15 |
| Every allowlisted or recorded deviation | the gate (re-measured every run) | A1–A3; no leftover | A, B |

### R7 pass-4 RF items on R8 (R8P1-RF-02)

- **P4-RF-01** (R7 C11, unstitched GND pieces 0.5–1.0 mm wide): **open, recorded as C15** (gate method 6 / 14 on the final
  board against R7's 13 / 37; the radio-bus finger trimmed by G7, D90).
- **P4-RF-02** (no gate held the GCPW coplanar ground, the F.Cu under the modules or where a trim lands): **closed in
  part.** `check_r8.strip_gcpw` hashes the F.Cu GND profile beside all eight RF tracks against R7's, and the
  `strip_gnd` / `strip_parts` / `strip_rule_areas` digests fail on any strip GND via, part or keep-out change; the F.Cu GND
  under U31 (79.77 mm²) and U30 (75.68 mm²) measured equal to R7's (pass 1). Still ungated: where a trim lands (G5 covers
  0.489 mm² of U31's courtyard, outside the module body; G7 lies in the radio bus forward of the fence).
- **P4-RF-03** (C302's relief, D30 / D31 seating): **closed on the copper** (rigid strip parts); D30.2 / D31.2 solid to
  the pour stays a recorded exception (C16); ORDERING §5 keeps the first-article seating inspection.

### Outside the list

- **Pyro review observations** (review pass 1 R8P1-PYRO-01 / -02 / -03, R8P1-REQUIREMENTS-04; review pass 2
  R8P2-PYRO-01 / -02 / -04, R8P2-REQUIREMENTS-01, R8P2-ROUTING-03; review pass 3 R8P3-PYRO-01 / -02 and the ACT_GATE
  findings of the planes, DFM, integrity, requirements and power passes (D109); DRC-legal; fail-safe directions are
  Inferences from the netlist and the resistor values). Every new net near the armed copper (PYRO1_BUS / IGN / OUT) and
  near the block's sense, gate and actuator-gate pads, and the battery-live and switch-defeating pairs, on the final
  board (measured on `c84f00b8…`, fix pass 3, whose copper changes left `pyro_neighbours.py`'s armed-copper neighbour
  list identical to fix pass 2's and near the actuator switch changed only R165's via; fix pass 4's `cc044ea0…` leaves the
  list and every pyro rule margin identical, its edits lying in the radio bus and at U11):

  | Neighbour | Closest (mask state) | One bridge or leak does | Direction |
  |---|---|---|---|
  | ACT_FET_S B.Cu pour (battery-live through Q120's body diode) | 1.089 mm to J124.1's bare bottom ring (step 9: 0.501; R7 1.200); 0.301 mm to the tented ARM1_SENSE via (14.55, 97.55) | to BUS: battery onto the bus with the switch open or closed, so the ARM link is bypassed; no fire unless Q124 also turns on; ARM1_SENSE reads armed with the link out. To the sense via: 8.4 V on PC5 through R170 4.7 kΩ (pin stress) | latent loss of the barrier: now at rule E's 1.0 mm, gated (D85); since fix pass 2 the gate also holds 1.0 mm from the drain PYRO1_OUT (D103), where battery copper is worse (it drives the igniter through the fitted link into RAW_ACT's load with the switch open, no Q124 needed); the drain's nearest battery copper is 3.562 mm (BAT_IN, R82.1–J121.1) |
  | RAW_ACT F.Cu pour | 1.115 mm to bare R127.1, PYRO1_GATE_N (step 9: 0.696; R7 1.042); 0.501 mm to bare C127.1, PYRO1_CONT (R7 0.950) | GATE_N: the gate rises to about 8.2 V through R126 / R128 and an armed channel **fires** (the one single bridge that does). CONT: 8.4 V into PC0 through R168 4.7 kΩ, about 1 mA, no fire | GATE_N ≥ 1.0 mm since D85; CONT benign, kept (its step costs 0.22 mm of the RAW_ACT neck) |
  | BAT_ENABLE F.Cu track (U9's EN / UVLO, R165 470 kΩ / R81 300 kΩ, 227 kΩ Thevenin) | 0.70 mm to both R134 pads (IGN / BUS, along y 98.45 for 25.5 mm, 24.6 mm inside PYRO_BLOCK); 0.216 mm to bare R175.2 (ARM1_SENSE); 0.40 mm to Q122.1 (ACT_EN) and Q122.3 (ACT_DRV); R81.1 1.825 mm from J121.1, bare to bare (B.Cu; 2.72 before fix pass 2 stood R81 west of the spine, D100); R165's BAT_ENABLE via (16.6, 104.5) 0.23 mm from bare Q120.9 (BAT_IN, B.Cu; 0.180 mm while it was a 0.6 mm via, R8 pass 2; the board's 0.5 mm signal via since fix pass 3, D108); BAT_ENABLE's nearest BAT_IN copper is now U9.1 to U9.5 / the feed lane, 0.200 mm (U9's own pin pitch) | to BUS / IGN when armed, or to ACT_EN: EN held high, so the power switch cannot turn the board off; a leak of about 1.7–2.0 MΩ or less from armed bus copper does the same (against R81, EN ≈ 1.1–1.2 V). To ACT_DRV with the switch open: EN ≈ 5.6 V, the board and RAW_ACT cycle on. To ARM1_SENSE: EN ≤ 0.75 V, the board will not start. To BAT_IN (Q120.9, the via): EN at pack voltage, the switch cannot turn the board off. To OUT: latched on through the cold pull-up, EN collapses when Q124 fires | defeats the power switch, which matters where it is the pad arming device (FMEA H-6(b), V-18); never fires by itself |
  | BAT_OVLO (R82.2) | 1.92 mm to J121.1, bare to bare, B.Cu | OUT high: U9's OVLO trips, the board browns out | no fire; loss of primary |
  | RAW_PROTECTED track | 1.975 mm to R134 | U9-limited supply onto BUS when on: link bypassed; no fire alone | latent |
  | BAT_DAMP (C89.2) | 2.45 mm to R134.1, bare to bare | IGN to GND through R166 0.33 Ω: armed, about 3.6 A in R134, which overheats; misfire | no fire; loss of primary |
  | ACT_GATE via | 2.52 mm to J124.1 | armed: the switch fights itself; link out: BUS fed through R120 100 kΩ, ≤ 77 µA | no fire |
  | GND (pours and step-7 vias) | rule D's 0.500 mm from the bare drain pads (Q124.5, R131.1, R173.1, J121.1), as R7; since step 7 two tented GND vias 0.528 / 0.537 mm from drain copper ((30.85, 91.5) to the PYRO1_OUT track, (31.65, 87.3) to bare R173.1; R7's nearest GND via to the drain 1.054 mm, Q124's rigid source via); since fix pass 2 R81.2, a bare GND pad (D100), 1.825 mm from J121.1's bare bottom ring (B.Cu), the drain's nearest bare GND pad (pass 2's board: R83.2 2.205 mm; R7: U7.8 1.630 mm), R5 L10 met (courtyard 1.58 mm; R8P3-PYRO-02); 40 GND vias in PYRO_BLOCK, nearest armed-live copper 0.522 mm (J121.2) | beside BUS / IGN or a gate / sense node: loads an armed bus or pulls the node low. **Beside the drain PYRO1_OUT it bypasses Q124:** with the link in and the switch on, the arming loop closes through the igniter (CIRCUIT_REVIEW; rule D's reason); a leak of about 24 Ω or less passes the MJG Firewire's 0.30 A no-fire current | **fires on the drain** (R8P2-PYRO-02); the plug-out cold test (FMEA H-1: a drain-to-GND path reads 0 mV) and ORDERING §5's static gate detect it before any real igniter |
  | ACT_GATE / ACT_DRV (the actuator switch's gate and its driver) | the chamfered B.Cu stub 0.264 mm from bare C120.1 (ACT_FET_S; masked track, fix pass 1's D91); the masked GND pours at the board's 0.15 mm zone clearance from all five bare ACT_GATE / ACT_DRV pads, 0.151 mm (B.Cu R120.2, C120.2; F.Cu R121.1, R121.2, Q122.3), as on R7 (Q121.4, R121.1 / .2, Q122.3); step 7's tented GND via (15.0, 107.3) 0.180 mm from bare R120.2, not the nearest GND copper; no GND pad within 1.0 mm of any of them (rule H's pad-to-pad intent met) | to ACT_FET_S: V_GS → 0, the switch held off. To GND: the switch turns on with the power switch open (rule H's reason, M3_R4), RAW_ACT live; no fire alone (Q124 stays off) | C120.1: fail-safe (R8P2-PYRO-04). GND: latent loss of the power switch's hold on RAW_ACT, a bridge needing a mask breach; REQUIREMENTS' accepted gate-net spacing outside the pyro block, R7's class (D109; fix pass 2's "move the via" candidate would gain nothing and is closed). Screened by ORDERING §5's 20 power-switch cycles with the link in (RAW_ACT below 1 V between them, every board) and its hot RAW_ACT check (below 0.1 V with the switch open at ≥ 70 °C); the "RAW_ACT dead with the switch open" step runs only where the switch is the pad arming device. Closing the class would take a GND-to-ACT_GATE / ACT_DRV zone clearance in `m3.kicad_dru` (with `make_ground.clearance` and a DC_GND re-solve: the via carries 0.24 A of the servo return): an owner option, not proposed |

  Every bare-to-bare pair is ≥ 1.82 mm (R81.1 (BAT_ENABLE) and R81.2 (GND)–J121.1 1.825 mm since D100, then R82.2–J121.1 1.92 mm); the close items
  are masked copper beside a bare pad, so a bridge needs a mask breach (inside the coated block for R127, C127, R175 and R134). The latch class is not new (R7 had BAT_IN 0.35–0.40 mm
  from Q122's pads and BAT_SW_RETURN 1.125 mm from J121.2). Bench coverage (ORDERING §5): RAW_ACT dead and the board off
  with the switch open, link out and in (the Q122 and BAT_ENABLE cases); 20 power-switch cycles with the link in, RAW_ACT
  below 1 V and 3V3 below 0.3 V between cycles (the bus latch); the static and leakage gates (GATE_N / CONT leakage), the
  static gate repeated warm where convenient (pass-1 R8P1-PYRO-04: a hard GATE_N–ARM1_SENSE short leaves the gate near
  0.37 V with the MCU in reset); the plug-out cold test. BAT_ENABLE is not rerouted: that is a signal-family change (D58)
  and none of its bridges fires.
- **MARGIN_PRESCRIPTION P1-9** (≥ 10 mm, mirrored): not met as written; the owner-delegated D12 limits are met.
- **Bench and physical tests:** none done (STATUS "Needs the bench").

## Open after fix pass 4

- The owner's dated acceptance of this list (M2), or more work first; a ruling on C10. Passes 2, 3 and 4 found no
  Critical or Major (pass 4 on fix pass 3's board `c84f00b8…`, 0 Critical, 0 Major, 16 Minor), so the review condition of
  REQUIREMENTS "R8 acceptance" is met; fix pass 4's board `cc044ea0…` carries pass 4's two copper Minors as the routing
  reviewer trialled them (D110, D111), and review pass 5 re-checked it in build integrity, planes and routing (0 Critical,
  0 Major, 3 Minor); the other five dimensions were not re-run on it: a further re-check is the owner's call.
- Commit or tag the generator state on `m3-assy-r8` (`git add -A`) and record the commit beside `cc044ea0…` here and in
  STATUS (owner action, R8P1–R8P5-INTEGRITY); no reviewed state survives as a commit
  (`fix2_baseline_sha256.txt`, `fix3_baseline_sha256.txt` and `fix4_baseline_sha256.txt` hold the hashes fix passes 2–4
  started from; the coordinator's backups of `990c8040…` and `c84f00b8…` are outside the repository, and review pass 5
  verified that the latter rebuilds `c84f00b8…`; `cc044ea0…`, the state pass 5 reviewed, exists only in this worktree).
- Before ordering R8: U4 consigned; JLC's acceptance of five long-edge tabs on a 118 mm board without a forward rail
  (Inference, D35); a cost and stock run within 24 h (`FAB_NET=1 m3_design/r8_fab.sh`; it also re-binds
  `cost_check.json` to the current CPL `ef90bfa1…`, unchanged since fix pass 3).
- The R8 firmware binding (from the binding note) and every bench item in STATUS.
- Recorded for a later pass, not defects: the build's DC gate has no seeded test (R8P2-POWER-04 / INTEGRITY-04);
  `check_r8.via_paste` could be ratcheted to fail any new ring under 0.1 mm beyond today's 12 own-net pairs (R8P3-DFM-02,
  optional); R162 0.2 mm aft at the next buzzer-group placement change (C20); a GND-to-ACT_GATE / ACT_DRV zone
  clearance is an owner option, not proposed (D109); C19's width_change_junction wording (review pass 5's note). The
  four pass-4 Minors once marked not worth fixing (RF-02, POWER-02, DFM-02, INTEGRITY-02) were done in fix pass 4.
