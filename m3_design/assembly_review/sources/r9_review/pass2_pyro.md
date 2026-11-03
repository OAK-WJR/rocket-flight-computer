# R9 review pass 2: pyro and arming safety

Reviewer: independent, read-only. The only repository file written is this report. The board and schematic were never
saved. Board `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`4f841a0e44ebb1829ad7996dfe6320ed527fce1fdb1e5ff11658e0705b44ac14`; DRU `ea77b791…` and netlist `8b0e04ea…` unchanged.
All three were confirmed before and after the review. `git status --short` was identical before and after. The other
pass-2 reports appeared under `sources/r9_review/` during the review. That folder is untracked as a whole, so its status
line does not change.

Comparison boards:
- step 10's `fc3d5b34…`, extracted from the fix pass's backup (`r9review/orig/worktree_before_fix1.tgz`);
- R8 `cc044ea0…` (`git show 9c8179b:…`).

Both copies were deleted afterwards. `../rocket-flight-computer-r8`, `-r7` and `-r6` were not touched.

**Verdict: 0 Critical, 0 Major, 2 Minor**, both cheap to fix:
- **R9P2-PYRO-01 (human factors and records):** R9 puts the ARM and IGNITER terminals end to end as identical black
  bodies on one edge. A swapped or cross-paired harness then leaves the igniter on RAW_ACT with the link out. The records
  analyse only stray strands. The top face labels only the outer two of the four wire positions.
- **R9P2-PYRO-02 (records):** three pyro statements in ORDERING / STATUS / R9_VALIDATION are not true as written. They
  are siblings of R9P1-PYRO-02 that the fix pass did not reach.

Everything else checked holds:
- the arming break is complete;
- the gates are defined off in reset and unpowered;
- every DRU pyro rule holds with the recorded margins on all four layers, re-measured with my own predicates;
- the bridge table has no forbidden pair;
- the rule-H seeded suite is live;
- D18, D19 and D85 hold;
- P-1b, P-3, P-7, the new P-7b and the strict pad rules hold, and P-7 / P-7b fire on seeded defects on this board's real
  geometry;
- no foreign net lies within 3 mm of armed copper;
- the wire entries face x = 0, confirmed again against JLC's own footprint.

Labels used below:
- **Measured:** pcbnew on the boards above, with my scripts in the scratchpad `r9review/pyro2/scripts/`.
- **Datasheet:** a cited maker document.
- **Calc:** arithmetic from the cited values.
- **Inference:** reasoning that was not measured (AGENTS §2.5).

## 0. Previous findings in this dimension (pass 1, on `fc3d5b34…`)

| Pass-1 item | Status on `4f841a0e…` | Evidence |
|---|---|---|
| R9P1-PYRO-01: QSPI_IO2 0.25 mm in front of U1.3 | **Closed** | See below |
| R9P1-PYRO-02: coating record omits U1's pins and the 0.151 mm pours | **Closed** for the rows it named | See below; siblings remain (R9P2-PYRO-02) |
| R9P1-PYRO-03: JLC's pin-1 mark on our pad 2 | **Closed** | See below |

**R9P1-PYRO-01.** The run is now QSPI_IO2 F.Cu (12.0, 50.6)–(13.9, 50.6).
- U1.3's pad is 0.550 mm from it (Measured). check_r9 P-7b's `mcu_gate_pin` table: QSPI_IO2 0.55, 3V3 1.25, IMU_INT1
  1.369 mm.
- P-7b is live:
  - `test_r9_check.PyroRules.test_p7b_mcu_gate_pin` passes (synthetic board);
  - on a seeded scratch copy of this board, a QSPI_IO3 track 0.17 mm from U1.3's pad end (inside U1's courtyard) leaves
    DRC silent and fails P-7b (§1).

**R9P1-PYRO-02.** These now state U1.6 1.20 / U1.1 0.70 mm and the GND pours at 0.151 mm:
- R9_VALIDATION's coating row;
- ORDERING §5's coating paragraph;
- C19;
- REQUIREMENTS "Accepted risks".

Measured again: every bare pyro-gate pad is 0.1506 mm from the F.Cu GND fill, and the five actuator-gate pads the same
from the B.Cu fill.

**R9P1-PYRO-03.** ORDERING §4 now has:
- the order remark: "the square pad (our pin 1) is your pin 2 (pin 10 on J122) … do not turn these parts";
- the expected DFM query.

`tools/jlc_orient.py` `PAD_ALIAS` is the involution 1↔2 (J121 / J124) and 1↔10, 2↔11 … (J122). The C430601 entry in
`jlc_corrections.json` is theta 0, residual 0.0, next best 3.592 mm, so the placement is unambiguous. The CPL places J121
and J124 at rotation 90, equal to the board's.

**Pass-1 observations:** unchanged (the copper is identical), apart from 6 (the battery-lead records were corrected in
the fix pass). Observation 4, that the pyro sheet note omits PE5 as a sentinel, is still open and was not dispositioned:
§14.

**Regression check (Measured, `board_diff.py`, `fc3d5b34…` → `4f841a0e…`):**
- No CH1 part, pad, track or via changed. The PYRO_BLOCK outline is identical.
- The changes near the pyro copper:
  - QSPI_IO2's three segments (above);
  - the F.Cu GND fill under U1 beside them (XOR 0.57 mm², x 11.75–13.65, y 50.26–50.85);
  - R9_RAW_ACT_F's west edge, now 29.75 to y 76.6 (0.35 mm² of RAW_ACT removed at x 29.40–29.75, y 75.60–76.77, beside
    the ARM1_SENSE lane's turn). The RAW_ACT_F fill now stands 1.120 mm from ARM1_SENSE, against fill margin A's 0.75.
  - TP120's two RAW_ACT vias, replaced by one at (31.5, 78.2).
  - None of these reduces a pyro margin.
- Every other change lies at x ≥ 24 outside the block, or in the RF strip: C98, USB_LIMITED, the three ground-aid vias,
  U31's vias and TXEN.
- Tools, compared against the pre-fix backup:
  - unchanged: `r9_pyro.py`, `r9_pyro_check.py`, `r9_route_pyro.py`, `bridge_table.py`, `rule_h_seed.py` and
    `check_actuators.py`;
  - `pyro_probe.py` changed only for determinism: sorted net names, and ties broken by `row < best`;
  - `check_r9.py` gained P-7b, and its other edits are R-5 / R-7 / R-8 / M-7.
  - So no pyro rule was relaxed, as the fix handoff states.

## 1. Gate and test runs (this pass)

**`tools/check.sh`** (GUI session logged in, no shim; `NUMPY_PY` = cfd venv): **exit 0** in 4 min 46 s.
- DRC 0 violations, 0 unconnected, parity 0, ERC 0;
- metadata / 3D audit OK; silkscreen inside the outline;
- fit OK: J121 / J124 1.23 mm; wire entry 6.4–7.0 mm at 5 mm height;
- rule-H seeded suite OK;
- check_r9 OK on all 40 rules;
- route_check r9: 0 failing / 0 allowlisted / 0 leftovers;
- `actuator safety contract: OK`.

The reports are copied to scratch `r9review/pyro2/gate/`.

**Tests (KiCad Python):**
- `test_r9_pyro`: 19 OK.
- `test_r9_check.PyroRules`: 13 OK, `test_p7b_mcu_gate_pin` included.

**Rule-H seeded suite** (this run's `seed.json`, bound to `4f841a0e…`, `issues []`):
- pairs Q124.5–R129.2 (1.225 mm), R132.1–C129.1 (1.758 mm) and R177.1–R124.2 (2.054 mm, B.Cu);
- each seeded at 0.95 mm in 8 variants, each caught by DRC, check_actuators, LC-1 or pyro_probe;
- control DRC hits 0.

**Seeded copy (mine).** Four tracks were added with pcbnew to a scratch copy, with the project's `.kicad_pro` / `.kicad_dru`.
`kicad-cli pcb drc` was run on it, then `check_r9 --only P-0,P-7`, and the copy was deleted:

| Seed | DRC | check_r9 |
|---|---|---|
| A: RAW_ACT 0.40 mm (edge) beside the ARM1_SENSE lane x 28.53 | `Pyro A … clearance 0.5000 mm; actual 0.4000 mm` | P-0 rule A 0.400 |
| B: 3V3 0.40 mm beside GATE_N's 45° run | silent (rule G 0.3 holds) | **P-7**: "a short puts 3.23 V on the gate in reset; minimum 0.5 mm" |
| C: SERVO1_OUT 0.40 mm aft of the BUS bar | `Pyro F … actual 0.4000 mm` | P-0 rule F 0.400 |
| D: QSPI_IO3 0.17 mm from U1.3's pad end | silent (inside U1's courtyard) | **P-7b**: 0.170 mm, minimum 0.5 |

Every seed is caught by at least one gate. B and D show that P-7 and P-7b cover what DRC by design does not.

## 2. Arming break (AGENTS §2.1, §2.2; F7, F8)

**Netlist** (`8b0e04ea…`, Measured):
- PYRO1_BUS = {J124.1, R132.1, R134.2}; PYRO1_IGN = {J121.2, R134.1}; PYRO1_OUT = {C128.1, J121.1, Q124.5, R131.1,
  R173.1}; PYRO1_COLD = {D120.1, R131.2}.
- J124.2 is RAW_ACT, Q121's drain, after the actuator switch.
- No part other than J124 joins RAW_ACT to a bus, igniter or drain net.
- No test pad is on BUS, IGN, OUT or a sense node. The pads on these chains are TP120 (RAW_ACT), TP121 (ACT_GATE) and
  TP122 (PYRO1_GATE).
- The only other current path into the channel is H-1's cold pull-up. The BAT54A is common-anode: pin 3 is the anode
  on 3V3, pin 1 the cathode on COLD and pin 2 is NC. With the link out it gives about 0.19 mA (pass 1, Calc), against
  the ≥ 20 mA no-fire figure.

**Copper (Measured, own script `m2_rules.py` and `m4_purity.py`):**
- RAW_ACT's nearest armed copper is J124.2–J124.1, 2.480 mm, identical on F.Cu, In1, In2 and B.Cu. Their inner rings
  are flashed. This is the terminal's own 5.08 mm pitch less its 2.6 mm pads, and rule E (1.0 mm) holds with no own-part
  exemption.
- D18 exempts J124's own RAW contact by design (`check_r8.inner_power_pyro`, ARM_TERMINAL). The next inner RAW_ACT /
  BAT_IN copper is the In2 RAW_ACT zone, 4.953 mm from R131.1 (≥ 2.65).

## 3. Gates defined off in reset and unpowered (AGENTS §2.4; F6, F8)

**Gate network** (netlist; check_actuators 4 / 4b / 4c):
- U1.3 = PE4 → R126 220 Ω (0805) → PYRO1_GATE;
- R127 1 kΩ from GATE_N to GND;
- R128 10 kΩ and C126 220 nF from the gate to GND;
- Q124 AON7524;
- U1.2 / U1.4 / U1.5 are NC sentinels.

The binding note carries "Lock PE4 (GPIOE_LCKR) before any other GPIOE set-up" and the D6.8 bootloader order. The lock
also keeps PE4 off AF0 (TRACED1), which the pyro sheet note forbids ("Never enable TRACE on PE2-PE6").

**Datasheet:** AOS AON7524 Rev 1.1 (October 2023), https://www.aosmd.com/res/datasheets/AON7524.pdf, fetched this pass.
- p. 1: VGS ±12 V maximum; "ESD protection" (HBM Class 3B).
- p. 2, Electrical Characteristics:
  - VGS(th) 0.4 / 0.8 / 1.2 V (VDS = VGS, ID = 250 µA);
  - IGSS ±10 µA (VGS ±10 V);
  - RDS(on) ≤ 5.8 mΩ at VGS 2.5 V, ID 16 A;
  - Ciss 2250 pF, Crss 65 pF.

**Calc:**
- In reset (pins analog) R128 ∥ (R126 + R127) = 1.087 kΩ holds the gate within 10 µA × 1.087 kΩ ≈ 11 mV.
- At link insertion the drain step couples 8.4 V × 65 pF / (220 nF + 2.25 nF) ≈ 2.5 mV.

**Reset-voltage table** (check_r9 P-7, this run): every item outside U1's courtyard whose hard short puts ≥ 0.2 V on the
gate keeps ≥ 0.5 mm. The nearest are:

| Item | Distance | Reset voltage | Gate copper |
|---|---:|---:|---|
| U1.2 / U1.4 (no net) | 0.412 mm | 0 V | GATE_N |
| U1.1 QSPI_IO2 | 0.833 mm | 3.229 V | GATE_N |
| PYRO1_OUT | 0.950 mm | 3.3 V | Q124.4 to the C128 branch |
| C127.1 CONT | 1.017 mm | 0.408 V | the gate via |
| U1.6 3V3 | 1.305 mm | 3.229 V | GATE_N |
| the CONT run | 2.855 mm | 0.367 V | GATE_N |

My own scan (`m1_dump.py`):
- **GATE_N copper outside U1's courtyard** has no non-GND neighbour within 1.5 mm other than U1's own pins, the
  sentinels and the gate network's own pads.
- **The GATE_N stub inside the courtyard** (y 52.65–53.10) has only U1 pads within 0.8 mm: U1.2 / U1.4 0.251 mm,
  U1.1 / U1.5 0.750 mm. P-7 and P-7b each leave that stub out. It is closed by geometry: a foreign track cannot pass
  between the pad row's ends without touching it.

## 4. m3.kicad_dru pyro rules A–H, A2 and the strict pad rules (Measured)

`m2_rules.py` restates the DRU predicates independently of pyro_probe. It covers each rule's own-part exemptions, rule
G both with the DRU's whole-item scope and with P-1b's clipped scope, and the fill-margin minimum for pairs with a
zone. It measures every copper layer:

| Rule | Min | Closest (this pass) | Where | pyro_probe (P-0) |
|---|---:|---:|---|---|
| A | 0.5 | 0.730 | RAW_ACT via (27.45, 57.95) to the ARM1_SENSE lane, F.Cu; the RAW_ACT_F fill 1.120 (fill 0.75) | 0.73 |
| B | 0.5 | 0.819 | Q124.5 to the gate run x 9.125 | 0.82 |
| C | 0.3 | 0.577 | R131.1 / R132.1 / R173.1 tie | 0.577 |
| D | 0.5 | 0.769 track; fill 0.750 (0.7495–0.7498 on all four layers; my polygons err ≤ 0.001 mm outward) | Q124's source track; GND fill to Q124.5 / J121.2 | 0.751 |
| E | 1.0 | 2.480 | J124.2–J124.1 (own terminal), every layer | none within its 2.0 mm reach |
| F | 0.5 | none within 2.0 | — | none |
| G (DRU whole items) | 0.3 | 0.569 | GATE_N's 45° run to U1.2 / U1.4 | — |
| G (P-1b clipped) | 0.3 | 0.412 | GATE_N's last 0.2 mm outside U1's courtyard to U1.2 / U1.4 (C12) | 0.412 |
| A2 | 0.3 | none within 1.8 | — | none |
| H / H+ | 1.0 / 1.2 | 1.224 | Q124.5–R129.2 (C13, margin 0.025 on H+) | 1.225 |
| GS | 1.2 | 1.680 | R128.1–C127.1 | 1.68 |
| AG | 1.2 | 1.334 | R121.1–C88.2, B.Cu | 1.334 |

The DRU's order is unchanged. The four rules after H are the thermal-relief sizing, "RAW_ACT pins to pours" (GND
zones), J2's 0.508 mm and the test pads' 1.0 mm, and none can lower a pyro rule on this board. The test-pad rule's 1.0 mm
sits under fill margin E's 1.35 mm only for a BUS / IGN zone against a TP pad, and none exists. That is INTEGRITY-03,
still open.

## 5. Solder-bridge table (P-5; F8)

`bridge_table.py --all` (this pass): 134 exposed pairs under 1.5 mm, 66 of them a part's own pads, **0 forbidden**.

- **Fires-class pairs:** own-part only.
  - Q124.1/.2/.3/.4–Q124.5, 0.520 mm;
  - C128.1–C128.2, 0.650 mm;
  - U1.1–U1.3, 0.700 mm;
  - U1.3–U1.6, 1.200 mm.
- **Non-tolerated pairs between two parts:** 21, all at or above their thresholds. The nearest is Q124.5–R129.2,
  1.225 mm, against the strict 1.2.
- **Pairs under 1.0 mm:** the 19 listed in `r9.json` P-5, all tolerated classes:
  - a sense node or midpoint to GND;
  - a gate to GND;
  - a midpoint to its own node or drain.

## 6. D18, D19, D85 (K-power-pyro), independently

- **D18:** In1 / In2 RAW_ACT and BAT_IN, J124's own pads excepted, reach armed copper at 4.953 mm in plan view (≥ 2.65).
- **D85:** BAT_IN / ACT_FET_S on the same layer as armed copper: none within 6 mm. On any layer pair the nearest is
  7.163 mm, the ACT_FET_S B.Cu pour to R132.1 (≥ 2.5).
- **D19:** GATE_N to servo PWM copper: none within 4 mm on any layer pair (≥ 0.5).

## 7. Owner-adopted rules (owner decision 2)

- **P-1b:** rule G's condition carries `(A.intersectsArea('PYRO_BLOCK') || !A.intersectsCourtyard('U1'))`. P-1 OK.
- **P-3:** the nets touching the CH1 courtyards' hull + 1 mm (Measured):

  | Layer | Nets | Note |
  |---|---|---|
  | F.Cu | GND, RAW_ACT (the RAW bar), 3V3 (D120's feed), D120.2 (no net) | all allowed |
  | In1, In2 | GND, RAW_ACT | the RAW_ACT is only J124.2's own barrel rings, which P-3 excepts |
  | B.Cu | GND, RAW_ACT, 3V3A, ACT_GATE | P-3's 1.0 / 1.5 mm limits hold |

  check_r9 `foreign_nets {}`.
- **P-7 / P-7b:** §3 and §1.
- **The strict pad rules:** §4.
- **LC-1:** 0 overrides; the 16 zone clearances are floors only.

## 8. Block purity, exits, vias

- **X2 / X2b** (Measured, own script): no net other than the CH1 nets, GND and RAW_ACT lies within 3 mm of bus, igniter
  or drain copper, on the same layer or in plan view.
- **Exits** (`requalify_r9.json` `pyro.exits`):
  - GATE_N 11.97, CONT 14.47 and ARM1_SENSE 40.0 mm, all F.Cu without a via;
  - *_MCU lanes 2.86 / 2.12 / 2.24 mm.
- **The one pyro via:** PYRO1_GATE at (9.125, 61.955). It is flashed on F.Cu and B.Cu only. Its GND partner (10.425,
  62.45) is 1.391 mm away, centre to centre (AGENTS §3 ≤ 1.5).
- **GND vias:** 39 in PYRO_BLOCK; the nearest armed copper is R134.2, 0.801 mm.
- **Above-rail copper near the sense lines' MCU sides:** the nearest is USB_LIMITED's trunk, 1.500 mm from U1.33 /
  U1.34, unchanged (pass 1 observation 3).

## 9. Renumbered J121 / J124: pads, legends, harness and FMEA text

**Pads** (Measured):

| Pad | Net | Position | Pad shape |
|---|---|---|---|
| J124.1 | BUS | (10.1, 80.96) | square |
| J124.2 | RAW_ACT | (10.1, 86.04) | round |
| J121.1 | OUT | (10.1, 70.73) | square |
| J121.2 | IGN | (10.1, 75.81) | round |

- Both are at rotation 90 with the entry on local −y, so they enter from −x.
- The netlist values read "ARM CH1: BUS1 / RAW" and "IGNITER 1: E1- / E1+".
- check_actuators rule 1 reads nets by pad number.

**Legends** (Measured):

| Face | Legend | Box or centre | Owner |
|---|---|---|---|
| top | `IGN` | x 2.07–4.84, y 66.78–68.47 | — |
| top | `1:E1-` | x 5.71–10.49, y 66.68–68.38 | J121.1 by 5.08 |
| top | `ARM` | x 3.18–4.87, y 88.28–91.53 | — |
| top | `J124` | x 5.19–6.89, y 88.46–92.33 | — |
| top | `2:RAW` | x 7.45–9.15, y 88.50–93.18 | J124.2 2.64 against J1.4 3.45 |
| bottom | `2:E1+` | centre (8.1, 74.01) | J121.2 1.15 against J121.1 1.46, ownership 0.31 mm |
| bottom | `1:BUS1` | — | J124.1 1.15 against J121.2 2.30 |
| bottom | `J124 2-FUSE-1: ARM LAST` | — | matches the numbering (pin 2 RAW → fuse → pin 1 BUS1) |
| bottom | `J124: 5A FAST / 2S` | — | — |

- J121's designator is hidden, recorded in M3_R9 §"Silkscreen": the IGN word identifies it.
- **Harness text:** ORDERING §7, FMEA_REDUNDANCY's new R9 row (I-4 / V-16) and R9_DECISIONS D-S10-09 name pads by role.
  They agree with the board: aft to forward OUT, IGN, BUS1, RAW at 5.08 / 5.15 / 5.08 mm.
- **The IGN–BUS1 strand case** (R9P1-REQUIREMENTS-08) is analysed in the FMEA: "about 5.8 A into a 1 Ω e-match",
  Inference. The other two R9-specific harness errors are not: R9P2-PYRO-01.

## 10. Wire room and lead direction (P-11, owner decision 1)

- P-11: both entries −x, 6.353 mm to the bore wall (≥ 6.25). fit_check: 6.4–7.0 mm at 5 mm height.
- The repository's 3D model is a symmetric envelope box ("not vendor model"), so the entry side rests on the footprint
  and on JLC's footprint.

I fetched EasyEDA's footprint for C430601 again (easyeda.com component API, `CONN-TH_2P-P5.08_DB128L-5.08-2P-BK-S`):
- Its Document-layer glyphs lie at Y 2981.1–2989.5, against pads at Y 3000 (EasyEDA y down):
  - the two wire-opening rectangles;
  - the arrows pointing +Y into the body.
- That is our local −y. With theta 0 and rotation 90 the entries face x = 0 (west). This confirms pass 1.
- ORDERING §4's JLC 3D-preview check stays the order-time control.

## 11. Coating and leakage (P3; MARGIN_PRESCRIPTION §4.13)

The R9_VALIDATION / ORDERING figures check out (Measured, `m3_bare.py`):
- **Bare pyro-gate pads to bare armed pads of another part:** 2.354 (R126.2–C128.1), 2.465, 2.526, 2.628, 2.792, 3.199,
  3.817 and 4.354 mm (R126.1–C128.1).
- **Bare 3V3 or RAW_ACT pads of another part** within 6 mm of any gate pad: none. TP122's nearest always-live pad is
  R164.2 (3V3A), 5.680 mm.
- **U1's own pins:** U1.1 0.70 mm and U1.6 1.20 mm from U1.3.
- **GND pours:** 0.1506 mm from R126.1 / .2, R127.1, R128.1, C126.1 and Q124.4, and from C120.2, R121.1, Q121.4,
  Q122.3 and R121.2 (C19). R120.2 0.933, Q120.4 1.436, TP121 / TP122 1.001 mm.
- **Calc:** R127's 6.4 kΩ leak figure checks out: 3.3 V × 0.911 kΩ / (R + 0.911 kΩ) × 0.978 = 0.4 V at R = 6.44 kΩ.

The coat region's description is not right in one place: R9P2-PYRO-02 (b).

## 12. TP122

- Bottom, at (7.58, 63.5), 1.5 mm square.
- No via in the pad. B.Cu GND fill 1.001 mm away; GND via (7.0, 65.9) 1.399 mm.
- No bottom courtyard within 4 mm.
- The gate via's GND partner is 1.391 mm away.
- Nearest bare armed pad: J121.1's bottom ring, 5.201 mm.
- ORDERING §5 probes it for the leakage and bootloader gates and coats it last. The leakage-gate figure checks out: 5 mV
  across 1.087 kΩ from 8.4 V means R ≈ 1.83 MΩ.

## 13. Findings

### R9P2-PYRO-01 (Minor, worth fixing): the ARM and IGNITER terminals now form one row of identical bodies; harness swaps are unanalysed and the two middle wire positions are unlabelled on the top

**Requirement:**
- AGENTS §2.1: the ARM plug is a complete break.
- F8: pyro disarmed until the ARM plug goes in; "black … ARM (J124) and IGNITER 1 (J121) … told apart by their ARM
  and IGN legends … unambiguous pin legends".
- FMEA V-17's lesson: "silkscreen must print function names"; the R9 row of I-4 / V-16.
- ORDERING §7: "route and label the two harnesses so that they cannot be swapped".
- r9_plan priority 2: a robust design.

**Finding (Measured):**

| | R8 | R9 |
|---|---|---|
| J124 (ARM) | (10, 93.32), rotation 90, entry −x | (10.1, 83.5), rotation 90, entry −x |
| J121 (IGNITER 1) | (36, 93.32), rotation −90, entry +x | (10.1, 73.27), rotation 90, entry −x |
| Arrangement | 26 mm apart on opposite long edges, entering from opposite sides | the same black DB128L body on the same edge, end to end |

On R9:
- The centres are 10.23 mm apart, the bodies 10.16 mm wide and end-stackable ("two make the 4P envelope", footprint
  descr), and the courtyards meet at y 78.39.
- The four wire positions read as one 4-way block: OUT 70.73, IGN 75.81, BUS1 80.96, RAW 86.04.
- **Top-face legends:** only the outer two positions: `IGN` and `1:E1-` aft of J121, `ARM`, `J124` and `2:RAW` forward
  of J124.
- **The middle positions (IGN, BUS1):** their legends are on the bottom only (`2:E1+`, `1:BUS1`), and `2:E1+` owns its
  pin by 0.31 mm.
- **The strip beside the entries** (x 0.3–4.5, between the `IGN` word, which ends at y 68.47, and the `ARM` word, which
  starts at y 88.28) carries no top silkscreen and no pads. It has only five 0.5 mm GND vias at x 3.0 (y 69.5, 73.5,
  77.5, 81.5, 85.5), plugged as ORDERING §3 orders.

**Consequence (Calc from the netlist, Inference for likelihood).** The records analyse only stray strands. Two
plausible harness errors are not analysed:
1. **Swap (igniter into J124, fused link into J121).**
   - With the link out the igniter sits between RAW_ACT and BUS. BUS's only DC path is the ARM divider (11.2 kΩ), so
     both leads sit at ≈ RAW_ACT whenever the board is on.
   - A single fault of the igniter's BUS-side lead to GND then drives several amps through the igniter: 8.4 V over
     1–2 Ω plus the leads, against a 1 A all-fire. The ARM break does not prevent it.
   - The same chafe is harmless in the correct wiring. With the link out, IGN and OUT sit at about 1.1 V behind H-1's
     10 kΩ cold pull-up (3.0 V into the two 11.2 kΩ dividers in parallel). A lead fault to GND then passes at most about
     0.3 mA through the igniter.
2. **Cross-seam pairing (link across IGN–BUS1, igniter across OUT–RAW).**
   - The igniter sits on RAW_ACT from power-on. A fault of its OUT-side lead to GND fires it.
   - ARM_SENSE reads disarmed, and CONT reads ≈ RAW_ACT / 11.2.

Both are caught before arming only by firmware:
- FMEA F-14's negative ARM_SENSE check: in the swap ARM_SENSE reads ≈ 0.75 V at 8.4 V against the 0.4 V hazard limit.
- M3_R4 §3's healthy band: about 0.098 V cold against CONT ≈ 0.75 V.

No firmware exists yet. R8's layout made both errors much less likely, with different edges, opposite entries and
separate harness runs (Inference).

Not a Major:
- F8's legend clause is met by letter.
- The errors are detectable at power-up.
- A fire also needs a second fault or a FET / MCU failure (I-1 / I-5) before the crew acts on the hazard tone.

**Fix (cheap; silkscreen and records only, no copper):**
1. `m3_design/r9_post.py`: legend all four positions by role on the top, in the free west strip beside each wire entry.
   - Text: `E1-` at y 70.73, `E1+` at 75.81, `BUS1` at 80.96, `RAW` at 86.04, vertical, at x ≈ 0.8–2.6, clear of the
     x 3.0 vias.
   - Or bracket `IGN` over the aft pair and `ARM` over the forward pair, with a mark at the seam (y 78.39).
   - Let the terminal-legend search reach this strip; it lies just past D-S9-02's 6 mm from the pins.
   - Re-run K-legends and silk_check.
2. FMEA_REDUNDANCY's R9 row and ORDERING §7: add the two cases above, their consequence, and that F-14 and the CONT
   healthy band are what catch them. Ask for a polarized harness: distinct ferrule colours, or a labelled lead per
   terminal.

### R9P2-PYRO-02 (Minor, worth fixing, records): three pyro statements are not true as written (siblings of R9P1-PYRO-02)

**Requirement:**
- AGENTS §2.5: every figure measured, no unlabelled inference.
- ORDERING is the procedure the coater and the bench operator follow.

**Finding (Measured):**

**(a) ORDERING §5, static gate** says: "on R9 every neighbour of PYRO1_GATE_N within 1.5 mm outside U1's courtyard is
GND".
- U1's own pins are within 1.5 mm of GATE_N's copper outside the courtyard (check_r9 P-7 table, this run):
  - U1.2 / U1.4 (no net), 0.412 mm;
  - U1.1 (QSPI_IO2, modelled 3.229 V), 0.833 mm;
  - U1.5 (no net), 0.833 mm;
  - U1.6 (3V3), 1.305 mm.
- The source, `requalify_r9.json` `pyro.reset.gate_n`, leaves out U1's pads by design (D-S5-14), and R9_VALIDATION's row
  says so ("U1's pins excepted"). ORDERING does not.

**(b) ORDERING §5, coat list** says: "(the top-side parts inside the PYRO_BLOCK area, x 1.2–28.4, y 54.2–89.8 …)".
- That rectangle is the area's bounding box. The PYRO_BLOCK outline is an irregular polygon of 42 vertices, 599.9 mm².
- These top parts lie wholly in the rectangle but none of them in the outline (`m7_bbox.py`):

  | Part | Courtyard | In the rectangle | In the outline |
  |---|---|---:|---:|
  | J122 | x 17.88–28.12, y 58.16–65.83 | 76.84 mm² | 0 |
  | R150–R153 | — | 6.57 mm² each | 0 |
  | R168 | — | 1.24 mm² | 0 |

- A coater reading the rectangle as the region coats the base of J122, the 7.7 A servo header. Its mating surfaces are
  on the keep-off list two bullets later. P-10 checks the true outline, so the gate passes.

**(c) STATUS** says "bare gate copper ≥ 2.354 mm from bare armed copper (R8 1.027 mm)". **R9_VALIDATION's coating row**
says "bare pyro-gate pads to bare armed-live pads: 2.35–4.35 mm".
- Both leave out the FET's own gate pin: Q124.4 is 0.520 mm from its drain land Q124.5 (DFN, own part, bridge table).
- ORDERING's coating paragraph states it.

**Fix (one clause each):**
- (a): "every neighbour … outside U1's courtyard, apart from U1's own pins (U1.2 / U1.4 no-net 0.41 mm, U1.1 QSPI_IO2
  0.83 mm, U1.6 3V3 1.31 mm; hi-Z in reset), is GND".
- (b): "the PYRO_BLOCK area, an irregular outline inside x 1.2–28.4, y 54.2–89.8 that leaves out J122, R150–R153 and
  R168 (do not coat them)".
- (c): add "of another part (Q124's own gate pin 0.52 mm from its drain land)".

## 14. Observations (no finding)

1. **Sense lanes beside foreign vias.**
   - The ARM1_SENSE node lane (x 28.53, 40 mm) passes, all DRC-legal (0.15 mm board minimum):
     - a 3V3 via (29.05, 49.125) at 0.170 mm;
     - SERVO4_MCU (27.95, 54.9) at 0.230 mm;
     - BAT_FAULT_N (27.95, 49.9) at 0.230 mm.
   - The CONT lane passes a 3V3 via (14.05, 57.4) at 0.202 mm.
   - These are listed in `requalify_r9.json` `pyro.divider` neighbours with 0 mA into the pin.
   - A short only falsifies a reading. 3V3 on ARM1_SENSE reads armed (F-14 refuses) and loads 3V3 by 3.3 mA. There is no
     fire path and no pin overstress. No rule asks more.
2. **TP121 against PYRO_BLOCK.** TP121's pad (ACT_GATE, bottom) edge is 0.01 mm outside PYRO_BLOCK (pad y 85.11 against
   the outline's y 85.1). P-10's "no test pad in the coat region but TP122" passes by that margin. There is no physical
   effect: the bottom face is coated only at TP122.
3. **Pyro sheet note** (pass 1 observation 4, still open): "PE3 (pin 2) and PE6 (pin 5) are sentinels" omits PE5
   (pin 4), U1.3's other neighbour. The binding note's "NC (firmware: analog or driven low for sentinels)" covers it.
4. **D120's 3V3 feed and J122.2.** The 3V3 feed (F.Cu x 17.9) passes J122.2 (RAW_ACT through-hole pin) at 0.390 mm,
   above the 0.3 rule (C13).
   - A bridge there puts RAW_ACT on 3V3: FMEA I-5's class (MCU overvoltage, gate undefined while armed).
   - P-2's order (power, self-test, then the link) mitigates it.
   - C13 records only the margin, not the consequence. For the power reviewer.
5. **Rule G's whole-item scope.** GATE_N's 6 mm 45° segment ends 0.105 mm outside U1's courtyard (cap y 53.25 against
   53.145).
   - Were it to touch the courtyard, DRC's rule G would exempt the whole segment.
   - pyro_probe P-0 and P-7 clip at the courtyard and would still hold it.
6. **ORDERING line 3** still says R9 has had "no independent review pass". Pass 1 has run. For the requirements reviewer.
7. **Retained from pass 1:** `2:RAW` lies 0.25 mm inside J1's courtyard. J121's designator is hidden (recorded).

## 15. Scratch

In the session scratchpad `r9review/pyro2/`:
- `scripts/`: `geo.py`, `board_diff.py`, `m1_dump.py` … `m12_j122.py`, `seed.py`;
- `out/`: the text outputs;
- `gate/`: this run's check.sh reports.

Deleted after use:
- the extracted `fc3d5b34…` and R8 boards;
- the seeded copy;
- the SVG / PNG renders;
- the EasyEDA download;
- the temporary folder.
