# R7 review pass 6: requirements conformance and the owner deviation list

Reviewer: independent, pass 6, dimension "requirements conformance and owner deviation list".

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `1ffc2585cbbb2a49623a5010b2792500849f06989cf43e48fb3e56068cddf9df` (fix pass 5, `fix5_F6_handoff.md`). Schematic
  root `47057f7d…`, `telemetry.kicad_sch` `6615ba08…`, `m3.kicad_dru` `1674d58b…`. The SHA and `git status` were the
  same before and after this review.
- **Documents read:** REQUIREMENTS, ORDERING, MARGIN_PRESCRIPTION, FMEA_REDUNDANCY, AGENTS, M3_R7, R7_VALIDATION,
  STATUS; `fix5_F6_handoff.md`; `pass5_*.md`, `pass5_verdicts.json`.
- **Method:** read-only. Everything ran on a scratch copy of `assembly_review/` (`<scratchpad>/p6docs/ar/`) with
  KiCad 10.0.6 pcbnew, kicad-cli and the repository tools, bytecode writing off. Probe variants (`p6docs/v3v3/`,
  `p6docs/vraw/`) were edited, refilled with `pcbnew.ZONE_FILLER` and saved in the scratchpad only. The only
  repository file written is this report.

## 1. Summary

**Reproduced on the final board:**
- `tools/check.sh` exit 0. DRC 0, unconnected 0, parity 0, ERC 0; audit OK; silkscreen 0; R7 contract OK; routing
  hygiene "0 failing, 33 allowlisted, 0 stale …, 30 leftovers recorded (0 unrecorded, 0 stale), 0 out-of-date route
  figures, 0 removable … exceptions: OK"; actuators OK; fit OK (J9 mated 0.03 mm, C84 0.11 mm, C76 4.150 mm, TP30.1
  5.008 mm).
- Tests: check_shell 2, dc_solve 3, fab_validation 23, fit_check 23, maze_clearances 10, procurement 15, r6_check 17,
  r7_check 34, route_check 41 (168), quality_audit 21 under both Pythons (189, as STATUS says).
- Fab: `fab_manifest.verify_manifest` → 5 outputs bound to `1ffc2585…`; job file JLC041611-7628 (0.035 / 0.203 /
  0.030 / 1.03 / 0.030 / 0.203 / 0.035, ENIG, M3-ASSY-R7); `cost_check.json` $105.98, 52 extended, 12:36:57Z;
  `stock_check.json` short U4 only, U30 159, U31 460, C530661 3,299, both bound to BOM `3a0c2f12…` / CPL `c68dc2cb…`.
- Board counts: 1,777 tracks, 706 vias; no In1 track; 23 pour trims (F 9, B 13, In2 1); 90 hidden designators,
  identical to M3_R7's list; 162 visible designators, all ≥ 1.0 mm text and 0.15 mm stroke; no visible designator nearer
  another part's courtyard than its own (pass-5 ink-polygon method); via-in-pad only TP122 and J2.1.
- **Deviation list counts reproduce entry for entry:**
  - A (33) = `ALLOWLIST`, with the nearest-GND distances 2.23 / 3.18 / 2.93 / 1.65 / 2.60 / 1.65 / 3.57 / 2.11 / 1.71 mm;
  - B (30) = `LEFTOVERS`; every route figure = `ROUTE_FIGURES` (`measured_check` 0); every "in pour" length in B
    re-measured independently (`py/inpour6.py`, 5 µm steps) within 0.05 mm, for example CAM_5V_SENSE 27.13,
    LOGIC_SOURCE_ST 25.81, BAT_SW_RETURN 19.45 + 1.30 mm;
  - E: 180 critical (64 / 35 / 30 / 18 / 12 / 10 / 9 / 2) and 69 non-critical (29 / 20 / 11 / 7 / 1 / 1), matching
    `route.json`;
  - D1–D4, D6, D7 (tail 0.523 mm inside its fill), D9–D13, D16 (In1 empty) and D17 (courtyard test) are gone on the
    board.
- **IPC-2152 estimate (P5-DOCS-02):** the arithmetic reproduces. Brooks & Adam's coefficients match KiCad's
  `common/track_width_calculations.cpp` (external 215.3 / 2.0 / −1.15 / −1.0, internal 1 oz 200 / 1.9 / −1.10 / −1.52).
  RAW_ACT 2.18 mm / 35 µm → 55.3 °C; BAT_IN 3.71 mm / 30 µm → 31.2 °C; ACT_FET_S 2.15 mm → 56.3 °C; the 20 °C widths are
  5.29 mm (outer) and 5.56 mm (In2).

**Pass-5 findings in this dimension (section 2).** P5-DOCS-02, -03 and -04 are closed; small residues are in
P6-DOCS-02 / -04. **P5-DOCS-01 is not closed.**
- (a) No owner acceptance is recorded.
- (c) One item of the pass-5 completeness table was not done: "Detours on poured nets (an M2 review item): only C7;
  not swept" (`pass5_docs.md` §4).

**Findings in pass 6: 1 Major, 3 Minor.**

- **Major P6-DOCS-01 (carries P5-DOCS-01): the deviation list is still not complete, so accepting it as written
  would not make M2 true.**
  - M2 gives review "detours and extra vias … on nets with a pour", and the gate does not test those nets at all. The
    list sweeps them for one item only (C7).
  - Part E's rationale for the poured critical nets' U-turns and layer hops, and Part F's dismissal of the pass-2
    scanner's chain detours, both say the gate holds them. For GND, 3V3, 3V3A, RAW_ACT and CAM_5V it does not.
  - The scanner finds 17 chain detours on poured nets: 1 is listed (C7), 6 more appear in E as U-turns under that
    wrong rationale, and 10 appear nowhere.
  - One unlisted case is measured as needless on a critical net. The 3V3 F.Cu run (31.1, 54.5) → (36.5, 51.65) is
    9.44 mm, dipping to y 56.05 where R6's removed C179.1 was. A two-segment redraw at the 6.58 mm octilinear minimum
    passes DRC 0/0/0, `route_check` with an identical instance set, `check_r7` and `check_actuators`, and has wider
    clearance (0.315 mm against 0.168 mm).
  - Also found: a 31.3 mm, 0.2 mm RAW_ACT B.Cu run that duplicates the pour path. Deleting it is clean and costs
    +0.03 mΩ.
  - STATUS's "the deviation list completed" overstates the list.
- **Minor P6-DOCS-02:** wording and like-for-like residues in parts A, B, D, E and F:
  - B9 and B23 are not reworded to "under the stricter rule";
  - the in-pour lengths of VCAP1 and VBUS are missing;
  - Part F's off-angle bound and "collinear" description are wrong, and five of the scanner's categories are not
    accounted for;
  - the C310.1 pad end that fix pass 5 created is called "judged by pass 4";
  - "15 removed" counts D18;
  - ACT_EN's hop has no reason.
- **Minor P6-DOCS-03:** C1's "why it cannot reasonably be removed" does not fit the RAW_ACT neck. The neck is set by
  an R6 GND via inside the RAW_ACT pour and the zone's notch at the servo header, not by the battery corner. Also,
  MARGIN P1-9 carries no R7 status line.
- **Minor P6-DOCS-04:** the remaining stale or loose items:
  - AGENTS §1 and §3 (already recorded for the coordinator);
  - `route_check.py`'s LEFTOVERS comment;
  - MARGIN's "all nine" in the 85 °C row and in R13;
  - two silkscreen legends that fell back far from what they describe: "J124: 5A FAST / 2S" at the RF strip, and R6's
    "UART 3V3 / RX-TX AT MODULE" beside J1.

**R7 acceptance (REQUIREMENTS, last section):**
- Met: `check.sh` and its contracts; M3 ($105.98, 52 of 52, 12:36Z); the fab binding.
- Not met: no open Critical or Major (P6-DOCS-01); M1 stock (U4 consignment, documented open).

## 2. Closure of the pass-5 findings in this dimension

| Pass-5 ID | Sev. | R7_VALIDATION disposition | Pass-6 check on `1ffc2585…` | Verdict |
|---|---|---|---|---|
| P5-DOCS-01 | Major | Partly fixed; open until the owner decides (l.531) | (b) Done: D items removed, D8 = A8, D5 / D14 / QSPI_IO0 in C17 (each inside its via copper: 0.283 / 0.141 / 0.212 mm from the via centre, radius ≥ 0.25 mm). (c) Partly: E holds every information-only instance (180 / 69, matching); C17–C19 hold the "kept" residuals; F scopes out `scan.py`. **But** the pass-5 completeness row "Detours on poured nets: only C7; not swept" was not addressed, and F justifies leaving it out with a gate coverage that does not exist for poured nets (P6-DOCS-01). (d) Done for 28 of 30 B rows (in-pour lengths reproduce); B9 and B23 keep absolute wording (P6-DOCS-02). (a) Not done: no owner acceptance | **Open**, carried as P6-DOCS-01 |
| P5-DOCS-02 | Minor | Fixed (records) | M3_R7 "High-current copper", C1 and F4 present. Arithmetic and coefficients verified (section 1). P1-9 recorded as not met in C1 / M3_R7. Residues: C1's removal reason does not fit the RAW_ACT neck, and MARGIN P1-9 has no R7 status line (P6-DOCS-03) | Closed (residue Minor) |
| P5-DOCS-03 | Minor | Fixed | MARGIN 85 °C row names U30 / U31 with their sources, "10 part classes". Residue: "all nine" stays in that row and in R13 (P6-DOCS-04) | Closed |
| P5-DOCS-04 | Minor | Fixed (records) | (a) A19, the P3 row and M3_R7 give net copper 53.33 mm / 6 vias and chain 47.53 mm; (b) NRST 46.11 mm in B19, M3_R7 and `ROUTE_FIGURES`; (c) 0.274 / 0.317 mm in M3_R7 and ORDERING §3, method named; (d) moot (D16 fixed) | Closed |

Items still recorded open and not raised again:
- P3-DFM-06(c), the "915MHZ ANT SMA" BOM comment, BOM line 36;
- P4-RF-01/-02; U4 consignment; the forward rail; the vibration estimate on the pass-2 board;
- `test_r5_repair`; the LS120 catalogue entry.

The sheet-15 notes are corrected (`telemetry.kicad_sch` l.1674 "37-48 mA … 25-38 mA", l.1681 "capacitive only while
R304 is 0R"), and the manifest is bound to the new sheet SHA.

## 3. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| P6-DOCS-01 | Major | REQUIREMENTS M2 (l.75): owner clean-routing criterion over the whole board; "What review checks: … detours and extra vias on non-critical nets **and on nets with a pour**"; "Deviations awaiting the owner's acceptance: every allowlist entry, every recorded non-critical leftover and **every review-only residual** is listed"; AGENTS §3; REQUIREMENTS "R7 acceptance". Carries P5-DOCS-01 / P4-DOCS-01 | **The deviation list still misses an M2 review category, so the owner's acceptance of it as written would not make M2 true** (and no acceptance is recorded either: P5-DOCS-01(a)).<ol><li>**The gate does not test detours or extra vias on poured nets.** These are GND, 3V3, 3V3A, BAT_IN, RAW_ACT, CAM_5V and ACT_FET_S, all critical by M2's definition. M2 therefore assigns them to review. The list shows no such review apart from C7. The pass-5 completeness table flagged exactly this ("not swept"), and the P5-DOCS-01 disposition does not mention it.</li><li>**The list says the gate covers them.**<ul><li>Part E, `u_turn`: "each net's length is held by the detour test (gated on critical nets …)".</li><li>Part E, `short_layer_hop`: "each net's via count is gated (critical) …".</li><li>Part F: "the M2 items among them (detours, extra vias, jogs) are measured by `route_check` in A, B and E".</li></ul>None of these holds for a poured net: 7 of E's 18 critical U-turns and 5 of its 9 critical layer hops are on poured nets, and F's 61 chain detours include 17 on poured nets.</li><li>**What lies in the gap** (pass-2 `scan.py`, unchanged, on the final board): 17 chain detours on poured nets. 1 is C7; 6 are in E only as U-turns, under the wrong rationale; **10 are in no part of the list**. They include an R7-era needless detour on 3V3 (measured removable, below), a RAW_ACT sense tap with 3 vias and an In2 run through the 3V3 plane, and GND runs of up to 7.3 mm for 4.9 mm.</li><li>**Measured needless detour on a critical net, R7 copper:** the 3V3 F.Cu run from via (31.1, 54.5) to the T at (36.5, 51.65). It still dips south to y 56.05, the spot of R6's C179.1 (R6 (35.725, 38.0) + 18 mm). C179 was removed in R7, and `r7_redraw.orphans` redrew "the trimmed C179.1 corner" along the old dip. A clean 2-segment route at the octilinear minimum exists (evidence). It is not in A–E and not counted by `route_check`.</li><li>**Duplicate copper accepted as a "U-turn":** RAW_ACT's 0.2 mm B.Cu run J124.2 → Q121.9 (31.29 mm, 9 segments, 11.65 mm inside the BAT_IN B.Cu pour outline) parallels the RAW_ACT F.Cu pour path that already joins J124.2 to Q121. It carries 2 % of the current. Pass 4 accepted it as a topological U-turn; E repeats that under the wrong rationale.</li><li>STATUS l.90–92 says P5-DOCS-01's list is "completed (every allowlist entry, leftover, review residual …)", and M3_R7 l.602–603 that what the gate does not judge "is in … parts C and E". Both overstate.</li></ol>Counter-argument: everything here is electrically negligible (DC drops of hundredths of a mΩ, slow or poured nets). The list is otherwise accurate and much more complete than in pass 5, and the owner could accept a scoped list. But M2 is the owner's acceptance criterion; its text puts poured-net detours under review; the list claims gate coverage that does not exist; and at least one omitted item is a measured, removable detour on a critical net. Accepting the list as written leaves M2 unmet, which is P5-DOCS-01's own test (upheld Major 2 of 3). | **Gate scope:** `tools/route_check.py` l.63–70: detour and extra_vias apply to "a net without a pour"; `net_route` l.906–907 "Route metrics of a net without a pour". Zones on the final board: GND (F, In1, B, In2 strip), 3V3_In2, 3V3A_In2, BAT_IN (B, F, In2, F crossbar), RAW_ACT (F ×2, B), CAM_5V_In2, ACT_FET_S_B (`py/zones.py`).<br>**List text:** R7_VALIDATION l.757 (`u_turn`), l.760 (`short_layer_hop`), l.771–784 (Part F), l.708 (C7), l.531 (P5-DOCS-01 row, item (c) does not mention poured-net detours). `pass5_docs.md` §4 table row "Detours on poured nets (an M2 review item) \| Only U12/C100 (C7); not swept".<br>**Gate run** (`p6docs/gate/route.json`):<ul><li>critical U-turns on poured nets: 3V3 B.Cu (36.94, 52.65) 16.32 mm (= C7); GND F.Cu (14.3, 59.0) 6.62, (16.35, 45.95) 6.56, (6.31, 79.625) 3.38; GND B.Cu (13.7, 80.6) 6.08; RAW_ACT F.Cu (10.4, 64.67) 5.60; RAW_ACT B.Cu (10.0, 90.78) 31.29;</li><li>critical layer hops on poured nets: 3V3 F.Cu (27.35, 44.25) 2.93 and In2 (30.63, 31.34) 2.40; 3V3A B.Cu (35.5, 76.54) 2.51; CAM_5V F.Cu (43.3, 33.43) 2.41 and B.Cu (39.35, 104.55) 0.95.</li></ul>**`scan.py` chain_detour on poured nets in no part of the list** (path / octilinear mm, `p6docs/scan2.json`):<ul><li>3V3 F.Cu (31.1, 54.5)→(36.5, 51.65) 9.44 / 6.58;</li><li>GND F.Cu (25.17, 109.8) 3.07 / 2.01; (6.31, 70.975) 2.76 / 1.36; (27.65, 29.85) 2.31 / 1.78; (25.97, 87.9) 2.19 / 1.58;</li><li>GND B.Cu (6.31, 79.625)→(6.8, 74.9) 7.30 / 4.93; (6.31, 79.625)→(6.01, 82.83) 4.95 / 3.33; (32.3, 55.7) 4.01 / 2.53;</li><li>RAW_ACT F.Cu (12.6, 81.27)→(7.6, 81.57) 7.11 / 5.12;</li><li>ACT_FET_S B.Cu (5.17, 96.0) 3.60 / 2.41.</li></ul>(The 3V3A (35.5, 76.54) one is E's hop.) The RAW_ACT sense tap runs R177.1 (F.Cu) → F/B via (13.7, 65.37) → B/In2 via (13.1, 75.97) → In2/F via (12.6, 81.27) → F.Cu U-path into the R6_RAW_ACT_F pour: 3 vias for an F.Cu pad to an F.Cu pour, with 3.53 mm of In2 inside the 3V3_In2 outline (R6 identical, `py/inpour6.py`).<br>**3V3 probe** (`p6docs/v3v3/`, `py/v3v3.py`):<ul><li>present: 5 segments, (31.1, 54.5)→(32.65, 56.05)→(34.7833, 56.05)→(35.0667, 55.7667)→(35.0667, 53.0833)→(36.5, 51.65), 0.25 mm, 9.436 mm; minimum clearance 0.168 mm to PULLPIN's via (35.17, 56.5);</li><li>redraw: (31.1, 54.5)→(33.65, 54.5)→(36.5, 51.65), 6.581 mm; minimum clearance 0.315 mm (GND via (35.85, 53.275)), then SERVO2_MCU via 0.470 mm (`py/gap.py`);</li><li>refilled; kicad-cli DRC with parity: 0 violations, 0 unconnected, 0 parity; `route_check`: OK, the same 312 instances (none added or removed); `check_r7` OK; `check_actuators` OK;</li><li>history: `m3_design/r7_redraw.py` l.145–148 redrew "the same branch at the trimmed C179.1 corner" as (31.1, 54.5)→(32.6, 56.0)→(34.65, 56.0)→(34.9, 55.75)→(34.9, 53.05).</li></ul>**RAW_ACT probe** (`p6docs/vraw/`, `py/vraw.py`):<ul><li>deleting the 9 B.Cu segments (10.0, 90.78)→…→(4.0, 105.98): DRC 0 / 0 unconnected / 0 parity; `route_check` OK; `check_r7` OK; `check_actuators` OK;</li><li>`dc_solve` RAW_ACT Q121:5–9 → J124:2 at 0.1 mm: 1.47 mΩ with it (B.Cu 2 % at mid-path), 1.50 mΩ without (F.Cu 100 %);</li><li>J124.2 and the via field lie in R6_RAW_ACT_F's single fill island (`py/island.py`).</li></ul> | <ol><li>Sweep the poured nets for M2's detours and extra vias. At least run the 17 `scan.py` chain detours and the poured-net vias with tracks on two layers.</li><li>Redraw the needless ones: the 3V3 run as measured; consider deleting the RAW_ACT B.Cu duplicate and shortening the RAW_ACT sense tap.</li><li>List the rest in C with a measured reason.</li><li>Correct E's `u_turn` / `short_layer_hop` rationale and F's "measured by `route_check`" for poured nets; or extend `route_check` with a chain-level detour test on poured nets.</li><li>Correct STATUS l.90–92 and M3_R7 l.602–603.</li><li>Then put the owner's dated acceptance on record.</li></ol> |
| P6-DOCS-02 | Minor | M2 (each item with a measured reason and "why it cannot reasonably be removed"); P5-DOCS-01(d) disposition ("reads 'no route found under the stricter rule' wherever the search could not have found the present route either"); document accuracy | Residues in parts A, B, D, E and F:<ol type="a"><li>**B9** (CAM_FAULT_N, 10.52 mm in an In2 3V3 void) still says "shorter only with two more vias". **B23** (SERVO2_OUT) says "shorter only with tiny jogs or two more vias". Both are absolute claims from the stricter-rule search.</li><li>The list preamble names only ARM1_SENSE and QSPI_IO2 among the part-A nets that run inside a pour outline. **VCAP1** (3.61 mm In2 3V3) and **VBUS** (13.81 mm In2 3V3, 2.97 F.Cu RAW_ACT, 2.44 B.Cu BAT_IN, 0.90 In2 BAT_IN) do too, and A31's "nothing shorter than 5.81 mm" comes from that stricter search.</li><li>**Part F** is inaccurate in three ways:<ul><li>"off-angle … within 0.00014°": the largest is 0.00744° (still rounding);</li><li>"collinear: its 3 are width changes at a junction": they are pad-entry necks at plain two-branch nodes, which M2 allows;</li><li>it does not account for `width_change_free` 18, `short_segment` 28, `net_length` 67, `width_change_at_pad` 17 or `width_change_at_via` 13.</li></ul></li><li>**Part E** `pad_end_offcentre` says the critical ones were "made one by one … by the pass-4 reviewer". But 3V3_RADIO's end 0.304 mm off C310.1 is new in fix pass 5 (from the D4 tidy-up) and was never judged.</li><li>**Part D** / STATUS "15 of the 18 removed" counts D18, whose RF-check half (P4-RF-02) stays open: 14 removed and D18 partly.</li><li>ACT_EN's 2.97 mm In2 hop (13.48, 106.06) is listed in E with no reason.</li></ol> | (a) R7_VALIDATION l.675, l.689; `py/inpour6.py` CAM_FAULT_N {In2:3V3 10.52}, SERVO2_OUT {}.<br>(b) l.609–611, l.653; `py/inpour6.py` VCAP1 {In2:3V3 3.61}, VBUS {F:RAW_ACT 2.97, B:BAT_IN 2.44, In2:BAT_IN 0.90, In2:3V3 13.81}.<br>(c) `scan2.json` `off_angle_rounding` SERVO3_MCU B.Cu (31.1463, 84.9936) `dev_deg` 0.00744, `lat_um` 0.07. `collinear_unmerged` (all `same_width` False):<ul><li>BAT_IN F.Cu (9.8, 40.85), 0.5 → 0.3 mm, 0.2 mm from U9.5 (pad x 10.0–12.4);</li><li>RAW_PROTECTED F.Cu (12.6, 40.35), same, at U9.6;</li><li>CAM_INPUT_LIMITED B.Cu (39.65, 87.6), 0.8 → 0.3 mm into U7.5.</li></ul>R7_VALIDATION l.771–784.<br>(d) `route.json`: `pad_end_offcentre` 3V3_RADIO F.Cu (36.565, 19.385) C310.1 `off_mm` 0.3041, absent from the pass-5 board's `rc_r7.json`; l.754.<br>(e) l.615–616, l.744; STATUS l.90.<br>(f) l.760. | Reword B9 / B23 with "under the stricter rule". Add VCAP1 / VBUS to the preamble and A31. Correct Part F's bound and wording, and add a line for the five unexplained categories. Name the C310.1 end as new and judge it. Say "14 removed, D18 partly". Give ACT_EN's hop a reason |
| P6-DOCS-03 | Minor | AGENTS §3 / M2 (IPC-2152); C1's "why it cannot reasonably be removed"; MARGIN_PRESCRIPTION P1-9 consistency | **C1 and M3_R7 give one removal reason for all three necks:** widening "needs the battery-corner copper re-laid … In2 carries the BAT_IN pour in the battery corner". That fits BAT_IN beside J1. It does not fit RAW_ACT, whose neck (2.18 mm at (19.5–20.95, 84.3–85.8)) sits about 20 mm from J1, at the servo-header end of RAW_ACT_F. There the fill is cut by two things: R6's GND via (18.975, 83.85), with its 1 mm track from C86.2, which stands inside the RAW_ACT pour; and the zone outline's notch at (21.0, 85.8). Whether moving that via widens the neck was not examined (Inference: it might, without a re-layout). **MARGIN P1-9 still reads as a live prescription with no R7 status line**: ≥ 10 mm mirrored, and 6.1 mm "allowed only locally at pad necks". The "not met since R6" is recorded only in C1 / M3_R7, unlike the "R14 (R7)" row | `RAW_ACT_F` outline (4.6, 81.2)…(24.5, 85.8)…(21.0, 85.8)…(21.0, 87.8)…(4.6, 87.8); fill at x 19.5: y 81.25–83.55 and 84.15–87.8 (the via's antipad); at x 21.0: 81.25–85.8 (`p6docs` inline scan). R6 has the same GND via at (18.975, 65.85). R7_VALIDATION l.702, M3_R7 l.827, MARGIN l.179–181 | State the RAW_ACT neck's real constraints in C1 and M3_R7, and say whether the C86.2 via can move. Add an R7 status line to MARGIN P1-9 (not met; necks 2.15–3.71 mm; C1) |
| P6-DOCS-04 | Minor | Document consistency (AGENTS, MARGIN, tool comments); REQUIREMENTS F8 / AGENTS §3 silkscreen ("terminal, arming and connector legends") | Stale or loose items:<ol type="a"><li>AGENTS §1 says the package was "regenerated … on the final fix-pass-4 board", and §3 still names four leftover categories. Both are recorded in R7_VALIDATION's open list for the coordinator, and still not done.</li><li>`route_check.py` l.282–283 says every non-critical "detour / extra_vias / tiny_jog / short_segment instance must have an entry", while `LEFTOVER_CATS = HYGIENE` (15 categories).</li><li>MARGIN's 85 °C row says "(10 part classes; R7)" but "at 70 °C all nine (and both R7 modules)", and R13 still says "all nine part classes".</li><li>Two silkscreen legends landed by `put(…, fallback=True)` far from their subject:<ul><li>"J124: 5A FAST / 2S" (B.SilkS (27.15, 21.9), at the RF strip's forward edge), about 66 mm from J124 (≈ y 88). R6 had it beside "J124 2-FUSE-1: ARM LAST" at the forward edge.</li><li>"UART 3V3 / RX-TX AT MODULE" (B.SilkS (26.15, 112.9), beside J1's legends), about 70 mm from J9, the only UART connector left. R6 had it with the J130/J131 module ports that R7 removed.</li></ul>Neither is ambiguous enough to mislead (one names J124; the other may still describe J9's TX/RX convention, Inference), but neither has been reviewed.</li></ol> | (a) AGENTS.md l.22 and §3; R7_VALIDATION l.804–806.<br>(b) tools/route_check.py l.282–285.<br>(c) MARGIN_PRESCRIPTION l.57, l.269.<br>(d) `py/facts.py` SILKTEXT list; `m3_design/r7_post.py` l.234, l.247 (targets (22, 60) and (23, 114)); R6 positions (22.9, 96.15) and (27.15, 1.4) | Update AGENTS §1 / §3, the tool comment and MARGIN's counts. Pin the two legends near J124 and J9 (or drop the UART one), or record why they stay |

## 4. Audit of "R7 deviations for owner acceptance" (R7_VALIDATION l.583–786)

| Part | Check | Result |
|---|---|---|
| A (33) | Entry for entry against `ALLOWLIST`; categories, positions, distances, figures | Matches. A1–A5's reasons are re-measured by `alt_audit` (0 removable), A6–A14's by `nognd_audit` (0), and the detour / extra_vias figures by `measured_check` (0). A8's 1.0 mm bare-pad keep-out is a real gated rule: `check_r7.foreign_clearances` applies it to every foreign track, via and zone fill. A15 / A20 state their in-pour lengths; VCAP1 and VBUS do not (P6-DOCS-02(b)) |
| B (30) | Against `LEFTOVERS` and `ROUTE_FIGURES`; in-pour lengths re-measured | Matches. 20 of 23 nets run in a pour void, as stated; the B7 / B22 measured blockers are stated. B9 / B23 wording (P6-DOCS-02(a)) |
| C (20) | Spot-checked C1, C7, C16, C17, C19 on the board | C17's four steps lie inside their vias' copper. C19's 0.9 mm BAT_IN run in C96.1 is present, continuing to (9.7, 54.025). C1: P6-DOCS-03 |
| D (18) | Every "removed / fixed" item on the board | True for D1–D4, D6, D7, D9–D13, D15–D17 (scan5 and pcbnew). D18: "partly" (P6-DOCS-02(e)) |
| E (249) | Counts against `route.json`; rationale | Counts match. The `u_turn` / `short_layer_hop` rationale is wrong for poured nets (P6-DOCS-01); the `pad_end_offcentre` rationale does not cover C310.1 (P6-DOCS-02(d)) |
| F | `scan.py` reproduced on the final board (945 instances, 591 critical, category by category as listed) | Counts match. The chain-detour claim is wrong for poured nets (P6-DOCS-01); the bound and wording slips are in P6-DOCS-02(c) |

**Would acceptance make M2 true?** Not yet. A, B, C, D and E cover what the gate counts and what earlier reviews kept,
with honest stricter-rule wording almost everywhere. They do not cover the M2 review item "detours and extra vias on
nets with a pour", and that item holds at least one measured removable detour on a critical net (P6-DOCS-01).
Everything else needed for the owner's decision is there.

**Fix pass 5's own new instances** (`route.json` against pass 5's `rc_r7.json`, and scan5 against `s5_r7.json`):
- PYRO1_GATE's no-GND layer change (A8);
- four extra-bend runs (band lanes, LED_RED, SERVO4_MCU);
- the C310.1 off-centre end;
- one width change at a T (USB_LIMITED).

All are counted in A or E. None is a §3 rule instance.

## 5. Requirement walk (final board `1ffc2585…`)

Verdicts: **Pass** (shown in the CAD, gate or fab files); **Fail**; **NV** (needs the bench, flight or firmware);
**Partial** (the CAD part passes and the rest is open).

| Item | Verdict | Evidence / remark |
|---|---|---|
| Sources: one primary pyro channel, isolated Blue Jay; 4-servo limit | Pass | `check_actuators`, `check_r7` OK |
| Sources: on-board MAX-F10S / E22, JLC-assembled; uplink cannot arm | Pass (CAD) | BOM C30005563, C5333985 SMT; R7 contract (`rf_part_coverage`, pad-level net check) |
| F1–F3, F5 | Pass (parts) | Unchanged circuits |
| F4 | Partial | DC solve reproduces (RAW_ACT 3.95; BAT_IN J1 → Q120 4.58 per F6). The IPC-2152 estimate is recorded and its arithmetic verified; no limit is set (C1, owner). Stall test is bench work. The RAW_ACT neck reason is in P6-DOCS-03 |
| F6, F7, F9 | Pass (CAD), bench NV | Unchanged circuits. The RAW_ACT → J124.2 path is 1.47 mΩ (the pour carries 98 %) |
| F8 | Pass (CAD), bench NV | DRC 0 under the nine pyro rules; ARM / IGN / BAT / CAM legends. Fuse legend placement: P6-DOCS-04(d) |
| F10 | Pass (CAD), bench NV | R7 contract OK. In1 has no track at all (stronger than "GND only in the strip"); the strip's In2 holds only GND and pass-through vias (`check_r7`) |
| P1 | Pass | 46 × 118 mm |
| P2 | Pass (CAD) | 5 supports; C76 4.150 mm; TP30.1 5.008 mm; vibration estimate carried from the pass-2 board (Inference, recorded) |
| P3 | Pass (procedure) | Unchanged |
| M1 | Pass, except U4 stock (allowed exception, open) | Job file JLC041611-7628, ENIG; stock U4 0, the rest in stock |
| M2: JLC rules, via-in-pad, silkscreen, courtyard | Pass | DRC 0. Via-in-pad only TP122 and J2.1 (as M2 names). Designators ≥ 1.0 mm text / 0.15 mm stroke. 0 visible designators nearer another courtyard |
| M2: clean routing | **Fail** | No owner acceptance; list incomplete (P6-DOCS-01) |
| M3 | Pass | $105.98 per board, 52 / 52, 12:36:57Z on 2026-10-18, bound to the BOM / CPL |
| R7 acceptance | Not met | P6-DOCS-01 open; U4 consignment |

## 6. Document consistency (beyond the findings)

These agree with one another and with the board:
- **Board SHA** `1ffc2585…` in STATUS l.12, M3_R7 l.4 / l.291, R7_VALIDATION l.25 / l.587, the manifest and `r7.json`.
- **Gate line:** STATUS, M3_R7 "Checks on the final board" and R7_VALIDATION "Final-board results" match this run's gate
  output. Test counts 168 + 21 = 189.
- **Cost and stock:** $105.98, $77.83 parts, 52 extended, U4 short, U30 159, U31 460, C530661 3,299. They appear in
  REQUIREMENTS M3, ORDERING §1 (l.28), M3_R7 and R7_VALIDATION; STATUS gives the cost and the U4 shortage.
- **Counts:** 1,777 tracks, 706 vias, 23 trims, 90 hidden designators; the placeholder at (23.65, 103.15) (ORDERING §3,
  M3_R7); 83 deviations, 10 §3 (STATUS, M3_R7, R7_VALIDATION).
- **REQUIREMENTS M2 "What the gate enforces"** against `route_check.py`: categories, scopes, `nognd_audit`,
  `measured_check`, `alt_audit` (allowlist and leftovers both audited, `main()` l.2265–2268), and the leftover rule.
  AGENTS §3 against M2, except P6-DOCS-04(a).
- **FMEA** I-11 / V-19; ORDERING §4 / §5; MARGIN R14 (R7). REQUIREMENTS F4 points to M3_R7's IPC section and C1.

## 7. Measurements and reproductions

All in `<scratchpad>/p6docs/`:
- **Gate:** `gate.log`, `gate/` (`route.json`, `r7.json`, `fit.json`, `drc.json`, `erc.json`, `audit.json`).
- **Tests:** `tests.txt`, with `status_before.txt` / `status_after.txt` identical.
- **Scans:** pass-2 `rg/scan.py` → `scan2.json`; pass-5 `p5rg/scan5.py` → `scan5.json`. Both diffed against pass 5's
  `p5rg/out/s5_r7.json` and `rc_r7.json`.
- **Board scripts:**
  - `py/facts.py`: counts, In1, trims, hidden designators, silkscreen;
  - `py/near.py`, `py/box.py`: copper near a point or in a box;
  - `py/zones.py`, `py/island.py`, `py/fillnear.py`: zone fills and islands;
  - `py/inpour6.py`: copper inside other nets' pour outlines;
  - `py/gap.py`: clearance of drawn segments;
  - `py/meas5.py` (pass-5 method) and `court.txt`: designator courtyard test.
- **Probes:**
  - `py/v3v3.py` → `v3v3/` (DRC, `route.json`, `r7.json`);
  - `py/vraw.py` → `vraw/` (the same);
  - `dc_solve.py` on `ar/` and `vraw/` (RAW_ACT Q121 → J124:2).
- **Fab:** `fab_manifest.verify_manifest`; the zip unpacked to `gz/` (job file, drills).

## 8. Sources

- Repository documents, by line:
  - REQUIREMENTS (F4 l.54, M2 l.75, M3 l.76, R7 acceptance l.105);
  - R7_VALIDATION (l.531, l.583–786, l.788–828), M3_R7 (l.527–668, l.783–827, l.861–884), STATUS (l.9–22, l.88–93);
  - AGENTS (§1 l.22, §3), MARGIN_PRESCRIPTION (l.57, l.179–186, l.269, l.271), ORDERING (l.28, l.60), FMEA (l.18,
    l.71);
  - `fix5_F6_handoff.md`, `pass5_docs.md` §4, `pass5_verdicts.json`, `pass4_routing_geometry.md` l.335–350;
  - `tools/route_check.py` (l.63–70, l.144–165, l.282–285, l.392–403, l.1832–1945, l.2225–2290), `tools/check_r7.py`
    (l.157–190), `tools/dc_solve.py`, `tools/fab_manifest.py`, `m3_design/r7_redraw.py` (l.122–165),
    `m3_design/r7_post.py` (l.215–252).
- KiCad source, Brooks & Adam coefficients:
  https://gitlab.com/kicad/code/kicad/-/raw/master/common/track_width_calculations.cpp (the "BA_COEFFICIENTS" table,
  "Brooks & Adam fit dT = K * I^a * W^b * Th^c to the IPC-2152 data (Table 3-1)"). The installed 10.0.6 help page
  still says the track-width tool uses IPC-2221; the claim in M3_R7 rests on KiCad's current source.
- JLC data as captured in `fab/cost_check.json` and `fab/stock_check.json` ("jlcpcb.com selectSmtComponentList",
  2026-10-18 12:36:57Z / 12:37:58Z).

## 9. Inferences (not checked against a primary source)

- **P6-DOCS-01:** "needless" is measured only for the 3V3 run (clean redraw) and the RAW_ACT duplicate (clean
  deletion, DC +0.03 mΩ). The other 9 unlisted poured-net chain detours were not probed: some are surely forced or
  trivial (2.2 against 1.6 mm). None of them, the two measured ones included, has a credible electrical effect.
- **P6-DOCS-03:** that moving C86.2's GND via (18.975, 83.85) would widen the RAW_ACT neck without a re-layout is
  inferred from the fill geometry, not probed.
- **P6-DOCS-04(d):** whether the "RX-TX AT MODULE" legend still describes J9's pin naming was not checked against the
  camera's documentation.
