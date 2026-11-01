# Design history

A short record of decisions that were made and later reversed, so they are not re-litigated.

## 1. Single board → two boards → single board

- **REV-G (2026-09-03)**: one 46 × 120 mm four-layer board (`GEOMETRY_REV_G.md`).
- **REV-H/M (2026-09-04)**: split into M1 (power + actuators, 46 × 50–66 mm) and M2 (MCU + sensors, 46 × 96 mm) joined by two JST PH harnesses (S12B-PH / S9B-PH, 21 wires). The argument was cost distribution: ~80 % of the BOM value (GNSS, MCU, IMU, barometer) sat on M2, while every open connector defect sat on the cheap power board, so power-board respins would be cheap.
- **M3 (2026-09-07 onward)**: the split was **reversed** — M1 and M2 are merged back into one board. Reasons: one assembly order instead of two (the fixed JLCPCB setup / stencil / feeder costs are paid once), no 21-contact inter-board harness, no hot-plug rule, and a shorter avionics bay (one board instead of 50 + 18 + 96 mm). The cost accepted: every respin now carries the full set of expensive silicon, and destructive power tests can no longer be done on a cheap sacrificial board.

The legacy M1 power/actuator design lives in `../reference/m1_power_actuator/` because its pyro, arming, servo, pull-pin and buzzer circuits still have to be merged into M3.

## 2. Rules from REV-H/M that still apply

- **M3 tie rods only clamp the bulkheads/sled and never pass through a PCB.** The board is fixed to the sled with its own M3 screws. (REV-G §7.4 had the rods pass through holes 112 mm apart in the plane of the board, which is geometrically impossible for a straight rod.) Hole positions are still open pending the sled design.
- **Connectors are not structural elements** (IREC DTEG 2026 V1.1 §6.12.3.2–6.12.3.3). Any harness connector needs an external retention means: one zip tie over the housing and a second anchoring the harness to the sled ~30 mm downstream. JST does not publish mating/retention force for PH, so the tie is the only defensible retention.
- **Separation targets on the MCU side**: buck switching loop ≥ 30 mm from the IMU; 25 MHz crystal ≥ 40 mm from the GNSS antenna (25 MHz × 63 = 1575.000 MHz, 420 kHz from L1 centre).
- **No switched high current across any boundary**: the 7.66 A servo bus and the 4.0–9.84 A pyro pulses stay in one compact corner.
- **Board placement is coplanar on the sled**: the envelope `h(x) = √(719.8489 − (x − 23)²) − 1.263` from `GEOMETRY_REV_G.md` is unchanged; the binding item is still the plugged servo header (23.50 mm needed, 1.558 mm margin).

## 3. Requirements history, R7–R9 (moved from current rows, R19-REQ-08)

Moved verbatim from `REQUIREMENTS.md` on 2026-10-31 so that each current row holds the rule and one R10 paragraph. Board hashes, costs and acceptance dates below apply to the named revisions only.

### M2: in-pad via exceptions (R6–R9)

Two exist: TP122's, and a named exception at J2.1, a 3V3 via inherited from R6 at (44.035, 77.92) whose 0.3 mm hole edge lies 0.14 mm inside J2.1's Ø0.787 mm opening. Both stay open and unplugged, and both are expected DFM queries (ORDERING §3, §4); J2 is taped and coated before flight (P3). **R8** (R8_DECISIONS D9): TP122's stays as the one named exception (AGENTS §3 instance A8); R8 has no via in J2's pads (the nearest via is 0.915 mm from a pad centre, measured on `429b6db4…`; fix passes 1–4 moved no via near J2), so the J2.1 exception lapses with R8. **R9:** TP122's in-pad via is gone (instance A8 removed: the gate via sits outside the pad, 1.391 mm from its GND partner via), and no via lies in any test pad or in J2's pads (review pass 1 moved the two RAW_ACT vias that opened into TP120, R9_DECISIONS D-F1-04; D-S10-14's exception lapses).

### M2: thermal-relief exceptions R4–R9

(exceptions listed in M3_R4 §2; R8: R8_VALIDATION C17; R9: R9_VALIDATION C21, J122's four GND pins solid for the 7.7 A servo return, where on R9's copper reliefs would not starve, and C20, the RF clamps' and DNP shunt lands' solid GND pads, the house relief rule's RF exception; R9_DECISIONS D-F1-06)

### M2: R7–R9 deviation-list acceptance

**Accepted by the owner on 2026-10-18** for board `c872a3d3…` (R7), with the 7.7 A servo-feed copper rise (R7_VALIDATION C1) accepted as estimated. **R8:** its list is R8_VALIDATION "R8 deviations for owner acceptance" (3 allowlist entries, 0 leftovers, 20 review rows, 91 information instances, and a "swept" line for every review category above, adjacency including pad-to-copper gaps since fix pass 2 and a margin-free bump and redraw search since fix pass 3, from `m3_design/assembly_review/sources/r8_design/step9/m2_sweep.py`), bound to `cc044ea0…`; **accepted by the owner on 2026-10-20**, including the C10 vibration item and the listed agent decisions. **R9:** its list is R9_VALIDATION "R9 deviations for owner acceptance" (0 allowlist entries and 0 leftovers under route_check's profile r9, review rows C1–C25 including the sixteen missed done rows of `r9_plan.md` §2 and review pass 1's additions, 114 information instances, the agent decisions, and a "swept" line for every review category above from `m3_design/assembly_review/sources/r9_design/step10/m2_sweep_r9.py`), bound to `4f841a0e…` (review pass 1's fix pass; step 10's list was bound to `fc3d5b34…`); **accepted by the owner on 2026-10-25**, including the agent decisions (U4 turned 180° with its new axis map, the crystal's local In2 GND plane), with the board kept at 102 mm.

### M3: R7–R9 cap and as-built costs; historical R10 snapshots

R7–R9 historical cap with on-board radio and GPS (F10, owner 2026-10-15): $84.41 + $42.00 = $126.41 per board, with the same 52-code limit** (`tools/jlc_cost.py`; it also reports the order price including JLC minimum purchases, which must not hide a large surcharge). The $42 allowance covers the RF strip at JLC prices, net of what it removes. R7 as built (`tools/jlc_cost.py` on the final board's fab BOM, live JLC data 2026-10-18 22:02Z, bound to the BOM/CPL in `m3_design/assembly_review/fab/cost_check.json `; the 08:29Z, 12:36Z, 15:30Z and 15:51Z runs gave the same, the 2026-10-17 21:01Z and 2026-10-18 02:59Z runs $105.96): **$105.98 per board** (parts $77.83 plus 92 unique codes × $1.53 / 5 boards; $77.83 of parts with JLC's minimum purchases, $79.23 on 2026-10-17 when J9 had a 23-piece minimum) **with 52 extended codes** (M3_R7.md): within the cap, at the code limit. The earlier 2026-10-16 05:14Z snapshot gave $110.93; U4 and U30 have since got cheaper. The RF strip's lines in the 2026-10-17 and 2026-10-18 runs: MAX-F10S $17.38, E22-900MM22S $6.52, two Kinghelm edge-launch SMAs $0.72, and the ESD diodes, bias limiter, ferrites, decoupling, interface resistors and pi network about $1.05 (no SAW). Against R6, R7 adds 14 unique codes (7 extended) and removes 4 (3 extended: R6's external radio/GPS ports and their port supply), a net +10 codes, +$3.06 per board in feeder fees (Standard charges every unique code, Basic or Extended). R6's parts total came from an older snapshot, so these lines do not reconcile the R6-to-R7 difference. U4 is priced at JLC's $8.39 (2026-10-17 and 2026-10-18), but JLC has none: consigning 7–10 parts at about $8.48 each (ST eStore, 2026-10-15) costs the owner $11.87–16.96 per board plus shipping instead, about $109.4–114.5 per board in all, still within the cap. **R8 as built** (`FAB_NET=1 m3_design/r8_fab.sh`, live JLC data 2026-10-19 23:51Z, 5 boards, bound to the R8 BOM / CPL in `m3_design/assembly_review/fab/cost_check.json `; the report names the step-9 CPL, `d26572d3…`, and the next `FAB_NET=1` run rebinds it to the current CPL, R8P3-REQUIREMENTS-04): **$106.00 per board, 52 extended codes**, the BOM identical to R7's (M3_R8). **R9 as built** (`FAB_NET=1 m3_design/r9_fab.sh`, live JLC data 2026-10-26 00:57–01:00Z on review pass 1's fix-pass board, 5 boards, bound to the R9 BOM / CPL in `m3_design/assembly_review/fab/cost_check.json `): **$109.38 per board** (parts $81.23 plus 92 unique codes × $1.53 / 5), **52 extended codes**, the BOM R8's line for line but the three footprint fields (M3_R9). Rerun `tools/jlc_cost.py` within 24 h of ordering (R7 acceptance; R8 acceptance; R9 acceptance). **Historical R10 owner-answer package, before the single-switch / AUD/GAP changes** (`FAB_NET=1 m3_design/r10_fab.sh`, live JLC stock 2026-10-28 18:29:21 UTC / cost 18:30:21 UTC, bound to the updated BOM / CPL): **$87.43 per board against $84.41**, a **$3.02 miss** (OQ-3 acceptance remains pending and does not block clean review), **47 unique extended / 36 basic codes** (83 total). Parts $62.03 plus 83 × $1.53 / 5 = $25.398 feeder share; parts with minimum purchases $63.83, approximately $89.23 with that feeder share before fixed fees. R430 (C185349): 17 in stock against a 3,610-piece minimum purchase, quote acceptance unconfirmed; U4 out of stock (0 against 5, consign). Cost / stock / procurement gates fail, while orientation, export, paste and manifest checks pass. The 2026-10-27 $87.01 snapshot predates R92 / R166 and is historical. **Historical R10 round-9 fix snapshot** (stock 2026-10-28T23:24:17Z, cost 2026-10-28T23:25:10Z, bound to the 82-code BOM / 215-row CPL): **$84.43 per board against the $84.41 cap, a $0.02 miss**, with **46 Extended / 36 Basic codes (82 total)**. Parts $59.34 plus $25.092 feeder share; minimum-purchase parts $61.14, approximately **$86.23 including feeder share** before fixed fees. R430 remains short (17 against 3,610 minimum) and U4 is out of stock (0 against 5). Cost / stock / procurement fail; export, orientation, paste and manifest checks pass. **OQ-3 is a known deviation, pending acceptance, and does not block a clean review round.**

### R7, R8 and R9 acceptance sections

#### R7 acceptance

M3-ASSY-R7 is accepted as a CAD and manufacturing-file candidate when: `tools/check.sh` reports zero DRC, unconnected, schematic-parity and ERC findings under the R7 contracts (`tools/check_r7.py`), with `m3_design/check_actuators.py`, `tools/fit_check.py` and the M2 routing check (`tools/route_check.py`) OK; an independent review pass finds no open Critical or Major issue; M3 is met (≤ $126.41 per board and ≤ 52 extended codes at 5 boards, `tools/jlc_cost.py` on a supplier snapshot no more than 24 h old) and M1 stock is met, U4 by consignment; and the fabrication outputs are regenerated and bound to the board by `tools/fab_manifest.py`. Status against these conditions: `STATUS.md` and `docs/R7_VALIDATION.md`. The R6 contract and checkpoint logs are in `docs/M3_R6.md`.

#### R8 acceptance

M3-ASSY-R8 is accepted as a CAD and manufacturing-file candidate when: `tools/check.sh` reports zero DRC, unconnected,
schematic-parity and ERC findings under the R8 contracts (`tools/check_r8.py`, which also holds R7's rigid copper by
hash), with `m3_design/check_actuators.py` (byte-identical to R7's), `tools/fit_check.py` and the M2 routing check
(`tools/route_check.py` profile r8) OK; two consecutive independent review passes (`r8_plan.md` section 4) find no open
Critical or Major; the owner accepts the R8 deviation list (M2); M3 is met on a supplier snapshot no more than 24 h old
and M1 stock is met, U4 by consignment; and the fabrication outputs are regenerated and bound to the board by
`tools/fab_manifest.py`. Status against these conditions: `STATUS.md` and `docs/R8_VALIDATION.md`. R8 was accepted on
2026-10-20 (M2) and is R9's fallback; R7 (accepted 2026-10-18) is R8's.

#### R9 acceptance

M3-ASSY-R9 is accepted as a CAD and manufacturing-file candidate when: `tools/check.sh` reports zero DRC, unconnected,
schematic-parity and ERC findings under the R9 contracts (`tools/check_r9.py`, rule-based in place of check_r8's hash
groups), with `m3_design/check_actuators.py` (pinned to its R9 version, which the R9 review loop reviews; its departure from owner decision 2's "check_actuators unchanged" is R9_VALIDATION part D's row D-S1-02), `tools/fit_check.py`, the plate model,
the seeded rule-H suite and the M2 routing check (`tools/route_check.py` profile r9, empty allowlist) OK; every hard row
of `r9_plan.md` section 2 is met; two consecutive independent review passes (`r9_plan.md` section 5) find no open
Critical or Major; the owner accepts the R9 deviation list (M2; R9_VALIDATION "R9 deviations for owner acceptance"),
dated; M3 is met on a supplier snapshot no more than 24 h old and M1 stock is met, U4 in JLC stock or consigned; and the
fabrication outputs are regenerated and bound to the board by `tools/fab_manifest.py`. Status against these conditions:
`STATUS.md` and `docs/R9_VALIDATION.md`. R9 was accepted on 2026-10-25: the owner accepted the deviation list (M2) with
the board kept at 102 mm; the gate, the hard rows and review passes 1 and 2 met their conditions; M3 and M1 were met on
the 2026-10-26 00:57Z (UTC) supplier snapshot, U4 in JLC stock; and the fabrication outputs are bound to `4f841a0e…`.
R9 is the revision to order after a fresh cost and stock run (ORDERING); R8 (accepted 2026-10-20) is its fallback.

### Moved in round 21 (R21-REQ-06)

#### M2: the R8 D10 detour amendment as worded for R8 (U31 body)

; **R8**, R8_DECISIONS D10: where an edge of that tree crosses a hard keep-out, that edge counts as the shortest octilinear path around it. A hard keep-out is an area closed to tracks on every copper layer the net can use, the U31 body for any non-GND net (F10), an NPTH hole or the board edge. Parts and other nets' copper never count as keep-outs, and the tool lists every net judged this way with both ratios)

#### M2: the R7–R9 pour lists

(on R8: GND, 3V3, BAT_IN, RAW_ACT, ACT_FET_S; on R9 also RAW_PROTECTED, an F.Cu pour; on R7 also 3V3A and CAM_5V; the tool reads the pours from the board's zones; the two net-level tests cannot judge these nets)

#### Board position: R9 aft-edge allocation

**R9:** aft edge at joint ≥ +80…+83 mm with the coax loops on the side away from the camera shroud, or ≥ +91…+95 mm with the loops entirely forward of the shroud;

#### Board position: R9 open position

R9's position remains open until its shroud geometry is measured

#### Board position: R7–R9 coax-loop zone

R7 fits the coupler bore along its whole length (P1, P2 CAD envelopes), so the bore no longer limits the position; the coax loop zone aft of the board and the camera shroud do. Allocate about 44–48 mm for that zone: jack 9.5 + straight plug about 16–20 + RG316 loops at 13 mm bend radius, axially staggered by at least one cable OD (two equal U-turns otherwise cross under the board), or right-angle plugs. Choose the plug and coax and cite the plug's drawing (the CAD's 16 mm plug envelope has none). The former "aft edge about 70 mm below the coupler's forward end" (joint +50) is superseded: it put the mated plugs inside the battery bay (`sources/r7_review/pass2_mechanical.md` MECHANICAL-03/04, `pass1_layout.md` L3).

