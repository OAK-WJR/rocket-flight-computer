# R7 review pass 7: requirements conformance and the owner deviation list

Reviewer: independent, pass 7, dimension "requirements conformance and owner deviation list".

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `4673c0a0f9fd290af694d6ca5a97e99b3b225466882ba5c6e57a9ad856b96ebd` (fix pass 6, `fix6_F7_handoff.md`). Root schematic
  `47057f7d…`, `telemetry.kicad_sch` `f5e1df83…`, `m3.kicad_dru` `1674d58b…`. The board, schematic, rules and netlist
  hashes and `git status` were the same before and after this review.
- **Documents read:** REQUIREMENTS, ORDERING, MARGIN_PRESCRIPTION, FMEA_REDUNDANCY, AGENTS, M3_R7, R7_VALIDATION,
  STATUS; `fix6_F7_handoff.md`; `pass6_*.md`, `pass6_verdicts.json`.
- **Method:** read-only. Everything ran on scratch copies (`<scratchpad>/p7docs/ar/` for the board, `p7docs/repo/` for
  the test suites) with KiCad 10.0.6 pcbnew, kicad-cli and the repository tools, bytecode writing off. Probe variants
  (`p7docs/v3v3via/`, `v3in2/`, `v3f/`) were edited, refilled with `pcbnew.ZONE_FILLER` and saved in the scratchpad
  only. The only repository file written is this report.

## 1. Summary

**Reproduced on the final board:**
- `tools/check.sh` exit 0: DRC 0, unconnected 0, parity 0, ERC 0; audit OK; silkscreen 0; R7 contract OK; routing
  hygiene "0 failing, 43 allowlisted, 0 stale …, 30 leftovers recorded (0 unrecorded, 0 stale), 0 out-of-date route
  figures, 0 removable … chain-detour exceptions: OK"; actuators OK; fit OK (J9 mated 0.03 mm, C84 0.11 mm, C76
  4.150 mm, TP30.1 5.008 mm).
- Tests: check_shell 2, dc_solve 3, fab_validation 23, fit_check 23, maze_clearances 10, procurement 15, r6_check 17,
  r7_check 34, route_check 45 (172), quality_audit 21 under both Pythons: 193, as STATUS says.
- Fab: `fab_manifest.verify_manifest` → 5 outputs bound to `4673c0a0…`; BOM `be711876…` (line 36 "GNSS ANT SMA; RADIO
  ANT SMA"), CPL `c68dc2cb…`; `cost_check.json` $105.98, 52 extended, 15:51:26Z; `stock_check.json` 15:31:32Z, short U4
  only; both bound to that BOM / CPL.
- Board counts: 1,747 tracks, 708 vias, no In1 track, 22 pour trims (F 9, B 12, In2 1), 90 hidden designators (the
  same list as M3_R7), every visible designator ≥ 1.0 mm text and 0.15 mm stroke; JLC placeholder at (23.65, 103.15).
- **Deviation list counts reproduce:** A = `ALLOWLIST` 43 (tiny_jog 2, critical_via_no_gnd 9, detour 9, extra_vias 10,
  chain_detour 8, pour_net_hop 5), with every A34–A46 length equal to `route.json`; B = `LEFTOVERS` 30; E = 250
  (176 critical: 63 / 35 / 30 / 16 / 12 / 9 / 9 / 2; 74 non-critical: 31 / 1 / 7 / 22 / 11 / 2, as listed); the
  u_turn and short_layer_hop attributions in E (5 poured-net U-turns = A34–A36, A38, A40; 11 non-critical hops on the
  named nets) match.
- **Pass-2 `scan.py` (unchanged) reproduces 918 instances and 50 chain detours (30 critical)**, and each of the 50, by
  location and length, is in A34–A41 (8), C24 (22) or C25 (20). The poured-net chain-detour sweep is complete.

**Pass-6 findings in this dimension (section 2):** P6-DOCS-02, -03 and -04(a)–(c) are closed. P6-DOCS-04(d) (two
misplaced legends) is recorded open for the board agent. P6-DOCS-01 is closed for the chain-detour part (gate,
records and Part E/F rationale) and its owner acceptance is, as recorded, still open; but its "sweep the poured nets
for extra vias and layer hops" part is not complete (P7-DOCS-01).

**Findings in pass 7: 1 Major, 2 Minor.**

- **Major P7-DOCS-01: an unlisted removable extra via, two overlap-only via joints and an uncounted 8 mm layer hop
  on 3V3, so accepting the list as written would still not make M2 true.**
  - Two 3V3 vias 0.948 mm apart, (30.17, 71.17) and (30.4, 70.25). Each via's ring is crossed by the other's track,
    0.195 mm deep and 0.230 mm from its centre, with no node: on In2 for (30.17, 71.17), on B.Cu for (30.4, 70.25).
  - The second via exists only to start an 8.00 mm In2 run (F → In2 → F). A 0.813 mm F.Cu stub T's it onto the
    diagonal that already ends in the first via.
  - The gate cannot see it:
    - `detour` / `extra_vias` skip poured nets;
    - `pour_net_hop` drops the via because the overlapping B.Cu track is a third "near" track;
    - `short_layer_hop` stops at 3 mm;
    - no category tests a track body overlapping a same-net via.
  - It is in no part of A–F. Part F's "close same-net vias are a defect only when their rings overlap" covers this
    pair (`scan.py` `via_pair_close`) and is wrong for it.
  - Probe: removing the second via and its stub, and starting the In2 run at the first via with one 0.325 mm diagonal,
    gives DRC 0 / 0 / 0 with parity, an identical `route_check` instance set (323), `check_r7` OK and
    `check_actuators` OK.
  - Five GND vias are likewise overlapped by GND tracks with no node (all inside GND fill, cosmetic), also unlisted.
  - STATUS's "measured every remaining local detour and layer hop the gate does not judge" overstates.
- **Minor P7-DOCS-02: C23's facts and the owner summary are not accurate or like-for-like.**
  - C23 calls (27.35, 44.25) and (35.5, 76.54) "the first via in the … fill". In each hop, both vias lie in the same
    fill piece.
  - Two of C23's 3V3 hops are removable by deletion, as measured. Each passes DRC 0 / 0 / 0 and `route_check` with
    nothing new. The In2 run lies wholly inside its own fill: the piece is 17.64 mm² before and after.
  - So the summary's "five removable" omits at least three items, counting P7-DOCS-01's via.
  - "98 listed deviations (A + B + C)" adds instance counts (A, B) to row counts (C). For example, 42 chain detours
    are 2 rows in C24 / C25, while A counts 8 chain detours as 8.
  - Plus two stale figures.
- **Minor P7-DOCS-03:** the P4-RF-01 row says "the final board has 23 … and 49" unstitched GND pieces, but C11
  measures 21 / 47 on the final board. ORDERING §1 and REQUIREMENTS M3 list the cost runs differently: 12:36Z against
  12:37Z, and ORDERING omits 15:30Z. Cosmetic.

**R7 acceptance (REQUIREMENTS, last section):**
- Met: `check.sh` and its contracts; M3 ($105.98, 52 of 52, 15:51Z); the fab binding.
- Not met:
  - no open Critical or Major (P7-DOCS-01);
  - M1 stock (U4 consignment, documented open);
  - M2 (no owner acceptance; the list is incomplete per P7-DOCS-01).

## 2. Closure of the pass-6 findings in this dimension

| Pass-6 ID | Sev. | R7_VALIDATION disposition (l.621–624) | Pass-7 check on `4673c0a0…` | Verdict |
|---|---|---|---|---|
| P6-DOCS-01 | Major | Fixed in the gate and the records; open until the owner decides | **Done:** `route_check` gates `chain_detour` (1.25 × / 0.5 mm, l.176–177, l.1786–1795) and `pour_net_hop` (l.1797–1832) on the 7 poured nets. Final board: 8 + 5 instances, all allowlisted (A34–A46), each length equal to the entry. The 3V3 C179 dip and the RAW_ACT B.Cu duplicate are gone. E's u_turn / short_layer_hop rationale and F's coverage statement are corrected. STATUS / M3_R7 are reworded. Every chain detour of `scan.py` (50) is in A34–A41 / C24 / C25. **Not done:** the extra-via / layer-hop half of the sweep. One 3V3 extra via with overlap-only joints and an 8 mm F → In2 → F hop escape both the gate and the list (P7-DOCS-01). C23's "first via in the fill" facts are wrong, and two of its hops are removable (P7-DOCS-02). Owner acceptance: none recorded | Chain-detour part closed; **residual raised as P7-DOCS-01** |
| P6-DOCS-02 | Minor | Fixed (records) | (a) B9 / B23 read "under the stricter rule" (l.836, l.850). (b) The preamble names VCAP1 and VBUS (l.755–756); A31 says "under the stricter rule". (c) Part F: 0.00744° / 0.07 µm, pad-entry necks, and the five categories accounted for (l.1012–1027). (d) C310.1 judged in E. (e) "14 removed or fixed, D18 partly". (f) ACT_EN measured (C26) | Closed |
| P6-DOCS-03 | Minor | Fixed (records) | C1 and M3_R7 give the RAW_ACT neck's own constraints (the C86.2 GND via and the zone notch; "not searched"). MARGIN P1-9 has an R7 status line (l.181–186) | Closed |
| P6-DOCS-04 | Minor | (a)–(c) fixed; (d) open (board) | (a) AGENTS §1 names the fix-pass-6 package; §3 covers every hygiene category and the poured-net tests. (b) The LEFTOVERS comment matches `LEFTOVER_CATS` (route_check l.339–344). (c) MARGIN's 85 °C row and R13 say "ten". (d) Still on the board. "UART 3V3 / RX-TX AT MODULE" (B.SilkS, ink x 14.14–38.16, y 112.05–113.75) runs directly along J1's pin row (pins x 15.38–30.62, y 110.4) on the bottom. Its subject (J130/J131) no longer exists, so from the bottom it reads as a label of the battery terminal. J1's top-side "1:BAT+ 2:GND 3:SW 4:SW" legends are correct. "J124: 5A FAST / 2S" sits at (27.15, 21.9), 73 mm from J124 | Closed except (d): open, correctly recorded (STATUS l.161–163, R7_VALIDATION "Open after fix pass 6"); fix it before the artwork is ordered |

Items still recorded open and not raised again:
- the owner's acceptance;
- C1's rise limit;
- P4-RF-01 / -02;
- U4 consignment;
- the forward rail;
- the vibration estimate on the pass-2 board;
- `test_r5_repair`;
- the LS120 catalogue entry.

## 3. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| P7-DOCS-01 | Major | REQUIREMENTS M2 (l.75): "no needless … extra vias or layer hops … overlapping or duplicate copper, joints made only by overlap", over the whole board, inherited copper included. "Deviations awaiting the owner's acceptance: … every review-only residual is listed … Each stays a deviation from M2 until the owner accepts that list". AGENTS §3; REQUIREMENTS "R7 acceptance". Carries P6-DOCS-01 item 1 ("the poured-net vias with tracks on two layers") | **A removable extra 3V3 via joined by copper overlap, and the layer hop it creates, are in no part of the deviation list and are invisible to the gate.**<ol><li>**Geometry.**<ul><li>3V3 via A (30.17, 71.17): F.Cu from (27.85, 68.85); B.Cu up to (30.17, 65.1) and down to (30.17, 73.7); no In2 track end and no fill.</li><li>3V3 via B (30.4, 70.25), 0.948 mm away: a 0.813 mm F.Cu stub to (29.825, 70.825), which is a T on via A's own F.Cu diagonal; an In2 run (30.4, 70.25) → (30.4, 78.25), 8.00 mm, to the 2-track via (30.4, 78.25) (then F.Cu to D120.3); no B.Cu track end and no fill.</li><li>The In2 run passes 0.230 mm from via A's centre: its copper overlaps via A's ring by 0.195 mm, with no node.</li><li>The B.Cu run (30.17, 65.1)–(30.17, 71.17) passes 0.230 mm from via B's centre: the same 0.195 mm overlap, with no node.</li><li>So two vias with parallel roles form a loop closed only by copper overlap, and via B is an extra via.</li></ul></li><li>**Removable (probe).** Remove via B and its F.Cu stub. Start the In2 run at via A with one diagonal (30.17, 71.17) → (30.4, 71.4), 0.325 mm. Results: refilled; DRC 0 / 0 unconnected / 0 parity; `route_check` OK with the identical 323-instance set (none lost, none new); `check_r7` OK; `check_actuators` OK. One via and 0.81 mm of F.Cu fewer, and both overlaps gone. The 8 mm In2 crossing itself is forced: F.Cu and B.Cu along x 30.4 hit SPI1_MOSI, IMU_CS, I2C1_SCL, SERVO3_MCU, SPI1_SCK, SPI1_MISO, I2C1_SDA and IMU_INT1. It still needs a listed reason.</li><li>**History.** In R6 the same cluster sat at (30.1, 53.17) / (30.4, 52.25). `r7_hygiene.v3v3` (l.1271–1299) treated "the B.Cu x 30.17 run passed 0.07 mm from the via (30.1, 71.17) without a node" as a defect and moved that via onto the run. Its docstring keeps "the vias still join both runs through the B.Cu run". That leaves via B overlapped 0.195 mm by the same run, and via A's In2 overlap grows from 0.125 (R6) to 0.195 mm.</li><li>**Why the gate passes it.**<ul><li>`detour` / `extra_vias` skip poured nets.</li><li>`pour_net_hop` counts a via as a pure layer change only when exactly 2 same-net segments lie within its radius (route_check l.1807–1808). The overlapping B.Cu run is a third, so via B is not pure, and the F → In2 → F hop (via B → via (30.4, 78.25)) is not counted.</li><li>`short_layer_hop` stops at 3 mm (l.1764–1766).</li><li>`overlap_only_joint` tests track ends only, and `via_overlap` tests via pairs only. Nothing tests a track body crossing a same-net via ring without a node.</li></ul></li><li>**Not in the list.** No row of A–F names (30.4, 70.25) or this hop; C23 lists only the `short_layer_hop` instances (< 3 mm). Part F dismisses `scan.py`'s 23 `via_pair_close`, this pair first among them, as "a defect only when their rings overlap". STATUS l.99–100 says the records "measured every remaining local detour and layer hop the gate does not judge (C17, C23–C26)". M3_R7 l.673–676 likewise lists what the gate still does not judge without this class.</li><li>**Same class on GND (cosmetic: every one lies inside GND fill on that layer, so the pour joins it), also unlisted.** Via (overlap) layer, of which R6 inherited the first three:<ul><li>(43.5, 89.0) 0.200 mm B;</li><li>(28.45, 25.85) 0.125 mm B;</li><li>(10.7, 70.5) 0.100 mm B;</li><li>(18.18, 90.55) 0.173 mm F, R7-era;</li><li>(22.85, 89.63) 0.070 mm B, fix pass 4's via.</li></ul></li></ol>Counter-argument: electrically negligible. One small via, the In2 crossing is forced, the overlaps are same-net, and the owner could accept a list that names them. But M2 makes every unlisted residual a standing deviation. This one is a measured removable extra via with overlap-only joints on a critical power net (the same test that upheld P6-DOCS-01 3 of 3). Two documents also assert that this class was swept | Board SHA `4673c0a0…`.<br>**Overlap scan** `p7docs/ovl.py` (same-net track body within a via's copper, no anchor, excluding chain neighbours), with `hops2_final.txt`:<ul><li>`3V3 In2 via (30.17,71.17) r 0.30 \| track (30.40,78.25)-(30.40,70.25) w 0.25 \| centre gap 0.230 overlap 0.195 \| via has 0 track ends on In2`;</li><li>`3V3 B via (30.40,70.25) \| track (30.17,65.10)-(30.17,71.17) w 0.25 \| gap 0.230 overlap 0.195 \| 0 track ends on B`.</li></ul>R6 run (`ovl.py r6.kicad_pcb`): `3V3 In2 via (30.10,53.17) … overlap 0.125`; `3V3 B via (30.40,52.25) … overlap 0.195`.<br>**Hop scan** `hops2.py` (M → L → M runs between 2-track vias on poured nets): `3V3 F->In2->F 8.00 mm (30.4,70.25) fill [] other-touch 1 -> (30.4,78.25) fill []`, the only poured-net hop not in A42–A46 / C23.<br>**Via detail** `viainfo.py`: (30.4, 70.25) F `->(29.825,70.825)`, In2 `->(30.4,78.25)`, B touch only; (30.17, 71.17) F `->(27.85,68.85)`, B `->(30.17,65.1)`, `->(30.17,73.7)`, In2 touch only.<br>**`scan.py`:** `via_pair_close 3V3 (30.17,71.17) d_mm 0.948 other [30.4,70.25]`.<br>**Probe** `probe_via.py` → `v3v3via/`: kicad-cli DRC with parity 0 / 0 / 0; `route_check` OK, `lost [] new []` against the gate's `route.json`; `check_r7` OK; `check_actuators` OK.<br>**Blockers** `p6docs/py/gap.py` on x 30.4, y 70.25–78.25: F.Cu collides with SERVO3_MCU, SPI1_MOSI, IMU_CS, I2C1_SCL and a RAW_ACT pad; B.Cu with SPI1_SCK, SPI1_MISO, I2C1_SDA and IMU_INT1.<br>**Records:** `grep "70.25"` finds nothing in R7_VALIDATION, M3_R7 or route_check; R7_VALIDATION l.1007, l.1030–1032 (Part F), l.887 (C23); STATUS l.96–102; M3_R7 l.670–676; route_check l.1764–1766, l.1797–1832; r7_hygiene l.1271–1299 | <ol><li>Remove via B as probed, or list the cluster in C with its measured reason.</li><li>List the 8 mm In2 crossing in C23 with its blockers. Its vias do not join the pour, so C23's heading needs widening, or extend `pour_net_hop` so that a merely overlapping track does not hide a pure via.</li><li>Add a `route_check` test for a same-net track body crossing a via's copper without a node (or list the 5 GND instances as cosmetic, in-pour).</li><li>Correct Part F's `via_pair_close` sentence, STATUS l.99–100 and M3_R7 l.673–676.</li><li>Then put the owner's dated acceptance on record.</li></ol> |
| P7-DOCS-02 | Minor | M2 (each item with a measured reason and why it cannot reasonably be removed); the owner summary's purpose ("the decision asked of you"); document accuracy | **C23's measured facts are wrong, two of its items are removable, and the owner summary is not like-for-like.**<ol type="a"><li>C23 says the 3V3 F.Cu hop via (27.35, 44.25) → via (29.9, 43.625), 2.93 mm, has "the first via in the 3V3_In2 fill". Both vias lie in the same fill piece (3V3_In2 #0, 455.3 mm²). For the 3V3A B.Cu hop it says "the first via in the 3V3A_In2 fill", but (35.5, 76.54) and (37.4, 76.52) are both in 3V3A_In2 #0 (28.2 mm²). Each hop's copper therefore parallels a plane connection that already exists.</li><li>**Removable (probes):**<ul><li>deleting the 3V3 F.Cu hop's three segments: DRC 0 / 0 / 0; `route_check` OK, which drops only its `short_layer_hop` and one `power_via_no_gnd`, with nothing new;</li><li>deleting the 3V3 In2 run (30.63, 31.34) → (32.33, 33.04): the same result. Fill piece #4 stays 17.64 mm² with both vias inside, so the run is wholly duplicate copper (C23 itself says it "duplicates copper the fill provides … not examined").</li></ul>The 3V3A hop (U4.5 → U4.8 / C31, a decoupling path) was not probed; it may be there for loop inductance (Inference).</li><li>The owner summary's "Removable but not removed" lists five items. With (b) and P7-DOCS-01's via it is at least eight, and C23's "judged by pass 4 (accept …); not re-searched" is the reason given for two of them.</li><li>"In all, **98 listed deviations (A + B + C)**" (STATUS l.17–21 "98 entries", M3_R7 l.7 "the recorded routing deviations (98 …)") adds instance counts (A 43, B 30) to row counts (C 25 rows). Several C rows hold many instances: C24 22 and C25 20 chain detours (A counts its 8 one by one), C17 12 steps, C15 about 25 adjacencies, C23 4, C5 7 crossings, C1 3 necks. Counted like A and B, the list holds about 190 items. The table's "25 rows" label is right; the sentence and the other documents read as 98 deviations</li></ol> | (a) `viainfo.py` output: (27.35, 44.25) `In2: fill ['3V3_In2#0 area 455.3']`; (29.9, 43.625) `In2: fill ['3V3_In2#0 area 455.3']`; (35.5, 76.54) and (37.4, 76.52) `fill ['3V3A_In2#0 area 28.2']`. R7_VALIDATION l.887.<br>(b) `probe_f.py` → `v3f/`: DRC 0 / 0 / 0; `route_check` lost `power_via_no_gnd 3V3 (29.9, 43.625)`, `short_layer_hop 3V3 F.Cu (27.35, 44.25)`, new []. `probe_in2.py` → `v3in2/`: "piece 4 area 17.64 via1 inside True via2 inside True", the final board's piece areas `[455.32, 74.51, 7.46, 10.33, 17.64]`, DRC 0 / 0 / 0, `route_check` lost `power_via_no_gnd` and `short_layer_hop` at (30.63, 31.342), new []. DC not re-solved (Inference: both vias join the same plane piece, which is wider than the 0.25 mm track).<br>(c) R7_VALIDATION l.712–721.<br>(d) R7_VALIDATION l.687–695, l.888–950; STATUS l.17–21; M3_R7 l.7 | Correct C23's via-to-fill facts. Judge or remove the two 3V3 duplicates. Add them (and P7-DOCS-01's via) to "Removable but not removed". State the list's size like for like (for example "98 entries and rows, about 190 items, of which A/B 73 instances"), or give C's instance count beside its row count |
| P7-DOCS-03 | Minor | Document consistency | <ol type="a"><li>R7_VALIDATION's P4-RF-01 row (l.436) says "the final board has 23 unstitched GND pieces narrower than 0.75 mm and 49 narrower than 1.0 mm". C11 (l.875), re-measured on the final board, says 21 and 47 ("were 23 / 49"). The row's "final board" is the fix-pass-4 board's figure left in place.</li><li>REQUIREMENTS M3 lists the same-result cost runs as "08:29Z, 12:37Z and 15:30Z". ORDERING §1 l.28 says "08:29Z and 12:36Z" and omits 15:30Z. The figures agree.</li></ol> | R7_VALIDATION l.436 against l.875; REQUIREMENTS l.76; ORDERING l.28 | Reword the P4-RF-01 row ("the fix-pass-4 board had 23 / 49; final board C11"); align the cost-run list |

## 4. Audit of "R7 deviations for owner acceptance" (R7_VALIDATION l.678–1035)

| Part | Check | Result |
|---|---|---|
| Owner summary | Counts, the 10 §3 instances, the removable list, the "needed before ordering" list | The A / B / E counts and the §3 list are accurate (A6, A7, A9–A14 re-searched by `nognd_audit` = 0; A8; C1). The removable list is incomplete and the total is not like for like (P7-DOCS-02). The ordering prerequisites match STATUS and AGENTS §1 |
| A (43) | Entry for entry against `ALLOWLIST` and `route.json` | Matches. A34–A41 lengths 16.32 / 6.62 / 6.56 / 2.31 / 6.08 / 4.01 / 5.60 / 7.11 mm and A42–A46 11.19 / 22.97 / 12.32 / 22.29 / 4.61 mm equal the gate's `path_mm`. A43's 22.97 mm includes the 10.71 mm In2 run from (7.9, 80.4) whose via the gate does not count as pure (the F.Cu diagonal's end lies 0.29 mm inside it); the description covers it |
| B (30) | Against `LEFTOVERS`; the P6-DOCS-02 wording | Matches; B9 / B23 reworded |
| C (25 rows) | C23 (poured-net hops), C24 / C25 (chain detours) against independent scans | C24 / C25: complete against `scan.py` (22 + 20 by location). C23: incomplete (P7-DOCS-01's 8 mm hop) and partly wrong (P7-DOCS-02(a)) |
| D (18) | Status line | "14 removed or fixed, D18 partly" holds |
| E (250) | Counts and attributions against `route.json` | Match, category by category and critical / non-critical |
| F | `scan.py` reproduced (918, 559 critical, category counts as listed) | Counts match. The chain-detour statement holds. The `via_pair_close` dismissal is wrong for the 3V3 pair (P7-DOCS-01) |

**Would acceptance make M2 true?** Not yet. Parts A, B, E and the chain detours of C24 / C25 now cover what the gate
counts and every chain detour on the board. One residual on a critical net is in no part of the list: the 3V3 via
pair with overlap-only joints, its removable second via and its 8 mm In2 hop (P7-DOCS-01). Accepting the list as
written would leave it a standing deviation. The rest of what the owner needs is there, with the corrections of
P7-DOCS-02.

**Further sweep, recorded and not raised:** `hops3.py` lists every M → L → M run between two-track vias on every net
(`hops3_final.txt`). On nets without a pour, hops of 3 mm and more inside the net-level `VIA_SLACK` of 2 are neither
gated nor named in M2's review clause, for example:
- ACT_GATE B → In2 → B, 11.03 mm;
- BUZZ_DRV, 4.00 and 13.37 mm;
- CAM_ILIM, 5.09 mm;
- SERVO1_OUT, 5.11 mm;
- PULLPIN, 21.16 mm;
- PYRO1_GATE_N, 37.0 mm;
- the QSPI F → B → F crossings.

M2 writes that slack into its own definition ("one crossing, under other copper and back"). So this is how M2 is
specified, not a list omission. The owner may want to know that M2 judges a single crossing per net on such nets
nowhere.

## 5. Requirement walk (final board `4673c0a0…`)

Verdicts:
- **Pass:** shown in the CAD, gate or fab files.
- **Fail.**
- **NV:** needs the bench, flight or firmware.
- **Partial:** the CAD part passes and the rest is open.

| Item | Verdict | Evidence / remark |
|---|---|---|
| Sources: one primary pyro channel and an isolated Blue Jay; the 4-servo limit | Pass | `check_actuators`, `check_r7` OK |
| Sources: on-board MAX-F10S / E22, JLC-assembled; the uplink cannot arm | Pass (CAD) | BOM C30005563, C5333985; R7 contract (`rf_part_coverage`, pad-level net check) |
| F1–F3, F5 | Pass (parts) | Circuits unchanged since fix pass 2 (root schematic `47057f7d…`) |
| F4 | Partial | DC solve reproduced in the records (RAW_ACT 3.98, BAT_IN 4.58, ACT_FET_S 1.36 mΩ). The IPC-2152 estimate is recorded (necks unchanged by fix pass 6, Inference in M3_R7). No limit is set (C1, owner). The stall test is bench work |
| F6, F7, F9 | Pass (CAD), bench NV | Circuits unchanged. RAW_ACT → J124:2 1.50 mΩ, now F.Cu only |
| F8 | Pass (CAD), bench NV | DRC 0 under the nine pyro rules; the ARM / IGN / BAT / CAM / GNSS / RADIO legends are present. The two stray legends are P6-DOCS-04(d), open: the UART legend lies along J1's pin row on the bottom |
| F10 | Pass (CAD), bench NV | R7 contract OK; J30–J31 18.69 mm apart (≥ 12); In1 has no track; J31's value is now "RADIO ANT SMA" (BOM l.36) |
| P1 | Pass | 46 × 118 mm (fit check) |
| P2 | Pass (CAD) | 5 supports; C76 4.150 mm; TP30.1 5.008 mm; vibration from the pass-2 board (Inference, recorded) |
| P3 | Pass (procedure) | Unchanged |
| M1 | Pass, except U4 stock (the allowed exception, open) | JLC041611-7628, ENIG; stock short U4 only |
| M2: JLC rules, via-in-pad, silkscreen, courtyard | Pass | DRC 0 (all severities); via-in-pad only at TP122 and J2.1 (`check_r7`); designators ≥ 1.0 mm / 0.15 mm |
| M2: clean routing | **Fail** | No owner acceptance; the list is incomplete (P7-DOCS-01) |
| M3 | Pass | $105.98 per board, 52 / 52, 2026-10-18 15:51:26Z, bound to BOM `be711876…` / CPL `c68dc2cb…`; rerun within 24 h of ordering |
| R7 acceptance | Not met | P7-DOCS-01; M2; U4 consignment |

## 6. Document consistency (beyond the findings)

These agree with one another and with the board:
- **Board SHA** `4673c0a0…` in STATUS l.12, M3_R7 l.4 / l.296, R7_VALIDATION l.28 / l.730, AGENTS §1 and the manifest.
- **Gate line and test counts:** STATUS, M3_R7 "Checks on the final board" and R7_VALIDATION "Final-board results"
  match this run (172 + 21 = 193).
- **Counts:**
  - 1,747 tracks, 708 vias, 22 trims (9 / 12 / 1), 90 hidden designators;
  - 43 / 30 / 25 rows / 250 (176 + 74);
  - 98 and 10 §3 (STATUS, M3_R7, R7_VALIDATION; the like-for-like caveat is P7-DOCS-02(d)).
- **REQUIREMENTS M2 "What the gate enforces" against `route_check.py`:**
  - chain_detour 1.25 × and 0.5 mm;
  - pour_net_hop's definition;
  - compound tiny jogs (k ≥ 2);
  - `alt_audit`'s non-plated-hole clearance (M2 "0.25 mm", code `NPTH_CLEAR` 0.26 = rule + 0.01 margin);
  - `measured_check` for chain-detour / series-hop entries.

  AGENTS §3 agrees with M2.
- **MARGIN:** P1-9 R7 status line (not met, C1); 85 °C row and R13 at ten classes.
- **ORDERING:** §1 cost and stock as `cost_check.json` / `stock_check.json`; §3 placeholder at (23.65, 103.15) (present
  on the board).
- **FMEA:** I-11 / V-19.
- **M3_R7:** the DC table and the fix-pass-6 change list match the handoff.
- **J31:** "RADIO ANT SMA" in the netlist, the BOM and the records (P3-DFM-06(c) closed).

## 7. Measurements and reproductions

All in `<scratchpad>/p7docs/`:
- **Gate:** `gate.log`, `gate/` (`route.json`, `r7.json`, `fit.json`, `drc.json`, `erc.json`, `audit.json`).
- **Tests:** `tests.txt` (and the reruns logged in this session); `status_before.txt`, `sha_before.txt`; both identical
  at the end.
- **Scans:**
  - `scan2.json` / `scan2.log` (pass-2 `rg/scan.py` against the R6 board extracted from `3b215ba`, SHA `184a87e8…`);
  - `facts.txt` (`p6docs/py/facts.py`);
  - `hops.py`, `hops2.py` → `hops2_final.txt` / `hops2_r6.txt`, `hops3.py` → `hops3_final.txt`;
  - `ovl.py` (via / track overlap, final and R6);
  - `viainfo.py`.
- **Probes** (scratch copies, refilled and saved there only):
  - `probe_via.py` → `v3v3via/` (`v3v3via_drc.json`, `_route.json`, `_r7.json`);
  - `probe_in2.py` → `v3in2/`;
  - `probe_f.py` → `v3f/`.
- **Fab:** `fab_manifest.verify_manifest` (5 outputs); `cost_check.json` / `stock_check.json` inputs and timestamps.

## 8. Sources

- **Repository documents, by line:**
  - REQUIREMENTS: M2 l.75, M3 l.76, R7 acceptance l.105.
  - R7_VALIDATION: l.436, l.605–624, l.678–1035 (owner summary l.680–724; C23 l.887; Part F l.1002–1035).
  - STATUS: l.9–23, l.96–103, l.155–171.
  - M3_R7: l.1–10, l.578–747, l.795–880, l.967–998.
  - AGENTS: §1, §3.
  - MARGIN_PRESCRIPTION: l.57, l.179–186, l.276.
  - ORDERING: l.28, l.60.
  - FMEA: l.18, l.71.
- **Handoffs and reviews:** `fix6_F7_handoff.md`, `pass6_docs.md`, `pass6_verdicts.json`.
- **Tools:**
  - `tools/route_check.py` l.63–122, l.148, l.176–177, l.339–344, l.1764–1766, l.1786–1832, l.2079;
  - `m3_design/r7_hygiene.py` l.1271–1299 (`v3v3`);
  - `tools/fab_manifest.py` l.46–61.
- **JLC data** as captured in `fab/cost_check.json` (jlcpcb.com selectSmtComponentList, 2026-10-18 15:51:26Z) and
  `fab/stock_check.json` (15:31:32Z). No datasheet limit was needed for this dimension's findings.

## 9. Inferences (not checked against a primary source)

- **P7-DOCS-01:** that the 3V3 via pair and the GND via/track overlaps have no electrical effect follows from their
  being same-net copper (the GND ones inside GND fill); not measured. The DC effect of removing via B was not solved.
  It is inferred negligible: one via and 0.8 mm of a 0.25 mm F.Cu stub on a branch also fed through via A.
- **P7-DOCS-02:** the DC effect of deleting the two 3V3 duplicates was not solved. It is inferred negligible or better,
  because both vias of each hop join the same plane piece. Whether the 3V3A hop is a deliberate decoupling path was
  not checked.
- **P6-DOCS-04(d):** that the UART legend "reads as a label of J1" from the bottom is a judgement of proximity: the
  ink lies 1.65 mm aft of J1's pin row along its full width.
