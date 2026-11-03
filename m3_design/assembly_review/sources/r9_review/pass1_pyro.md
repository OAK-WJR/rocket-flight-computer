# R9 review pass 1: pyro and arming safety

Reviewer: independent, read-only. No repository file changed except this report. The board and schematic were never
saved. Board `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`fc3d5b34a4bfbaecfbcb44bdf8144c87015fc71be7accf48354f23410e8d0f51`, confirmed before and after the review.
`git status --short` was identical before and after, apart from the new `sources/r9_review/` reports: this one and the
other pass-1 reviewers'. The netlist `schematic.net.xml` differs from R8's
(9c8179b) only in the Footprint fields of J121, J124 and J122: no net, value or pin changed (checked by script).

Comparison board: R8 `cc044ea0…`, extracted with `git show 9c8179b:…` into the session scratchpad
(`r9review/pyro/r8/`) and deleted afterwards. `../rocket-flight-computer-r8`, `-r7` and `-r6` were not touched.

**Verdict: 0 Critical, 0 Major, 3 Minor.** Each Minor is cheap to fix:
- R9P1-PYRO-01: a copper item. QSPI_IO2 runs 0.25 mm in front of the pyro gate pin U1.3. R8 kept it 0.75 mm away.
- R9P1-PYRO-02: records.
- R9P1-PYRO-03: order documents.

The arming break is complete. The gates are held off in reset and unpowered. Every pyro rule holds with the
recorded margins. The bridge table has no forbidden pair. The rule-H seeded suite is live. The CH1 column is the
cleanest pyro layout of any revision so far:
- no foreign net within 3 mm of armed copper;
- no foreign bare pad within 6 mm of J124.1 or J121.2 on either face.

Labels used below:
- **Measured:** pcbnew on the boards above (scripts in `r9review/pyro/scripts/`).
- **Datasheet:** a cited maker document.
- **Calc:** arithmetic from the cited values.
- **Inference:** reasoning that was not measured (AGENTS §2.5).

## 0. Previous findings in this dimension

This is the first pass on R9. The last pass in this dimension was R8 pass 4 (`sources/r8_review/pass4_pyro.md`, board
`c84f00b8…`).

**R8P4-PYRO-01** (Minor, records): rule G was missing from R8's `requalify.py` and from M3_R8's per-rule table.
- R9 measures all nine DRU pyro rules: `step10/requalify_r9.py`, `step10_evidence/requalify_r9.json` `pyro.margins`.
- That covers rule G: 0.412 mm, margin 0.112, GATE_N's entry into U1.3 against the no-net sentinels U1.2 / U1.4.
- R9_VALIDATION's requalification row and M3_R9's headline list G. R9_VALIDATION C12 records the 0.112 mm margin for
  the owner.
- **Closed.**

**Earlier R8 pyro items, re-checked as classes on R9:**
- **R8P1-PYRO-04** (the GATE_N lane 0.300 mm from the CONT lane, 0.37 V on a hard short): gone by geometry.
  - GATE_N to the CONT run is now 2.855 mm (check_r9 P-7 table).
  - Every copper item of another net within 1.5 mm of GATE_N outside U1's courtyard is GND (`r9_pyro_check.gate_neighbours`
    on the final board, below).
- **R8P2-PYRO-01** (battery copper beside the drain): none within the check's 3.5 mm reach.
  - check_r9 K-power-pyro `battery_pyro` nearest: null, against the 2.5 mm limit.
  - D85 now includes the drain.
- **R8P3-PYRO-01** (GND pours 0.151 mm from the bare actuator-gate pads): the condition persists on R9.
  - It measures 0.151 mm, the board's zone clearance (§11).
  - R8's record of it (D109, with an owner option) was not carried into R9's records. Folded into R9P1-PYRO-02.
- **R8P3-PYRO-02** (R81.2 in the GND row): R8-specific geometry, gone.
  - The drain's nearest bare GND pad on R9 is C128.2, 2.280 mm from Q124.5.
- **R8 pass 4 observation** (re-plug check after the bootloader static gate): now in ORDERING §5's Bootloader step.
  "Unplug USB and confirm the board is still in the bootloader: RADIO_NRST at R311.1 … below 0.66 V".

Status: closed or dispositioned, apart from the records gap in R9P1-PYRO-02.

## 1. Gate and test runs (this pass)

**`tools/check.sh`** with `NUMPY_PY` set to the cfd venv. A GUI session was logged in, so no shim was needed (`who`:
console). Exit 0:
- DRC 0 violations, 0 unconnected, parity 0, ERC 0;
- metadata / 3D audit OK; silkscreen inside the outline;
- fit OK: J121 / J124 1.23 mm; wire entry to the bore wall 6.4–7.0 mm at 5 mm height;
- plate model; rule-H seeded suite OK;
- check_r9 OK on all 40 rules, P-0 … P-11, K-power-pyro, LC-1 and R-13 included;
- route_check r9: 0 failing, 0 allowlisted, 0 leftovers;
- `actuator safety contract: OK`.

The reports were copied to scratch (`r9review/pyro/gate/`). The figures below from `r9.json` and `seed.json` are this
run's.

**`tools/test_r9_pyro.py`:** 19 tests OK (46 s). Each seeds one defect class:
- template; margins; the G exception; bridges;
- a fires-class pair at 1.12 mm;
- GATE_N neighbours;
- foreign copper near armed copper;
- route pending;
- the derived PYRO_BLOCK;
- the DRU fill margin.

**The step-5 gate's functions on the final board** (`m3_design/r9_pyro_check.py` `gate_margins`, `gate_bridges`,
`gate_neighbours`, `gate_sense`, `gate_armed`, `gate_template`, called on `fc3d5b34…`): all OK.
- The template: the CH1 copper still equals the pad-derived template after steps 6–9.
- No fires-class pair between two parts under 1.5 mm.
- GATE_N's only neighbour within 1.5 mm outside U1's courtyard is GND.
- No foreign net within 3 mm of armed copper.

These gates run in the build (steps 5–8). `tools/check.sh` holds only the 1.0 / 1.2 mm thresholds. Step 9 moved no pyro
copper. So this run confirms the final board still meets the stricter step-5 floors.

**Seeded DRC.** Method:
- a scratch copy of the board, `.kicad_pro` and `.kicad_dru`;
- three tracks added with pcbnew;
- `kicad-cli pcb drc --severity-all`;
- copy deleted.

KiCad loads R9's DRU and fires each seed:

| Seed | DRC result |
|---|---|
| RAW_ACT F.Cu track (12.0–15.0, 79.71), 0.65 mm from the BUS bar | `rule 'Pyro E: RAW_ACT to bus and igniter (ARM break)' clearance 1.0000 mm; actual 0.6500 mm` (and 0.5000 mm to J124.1) |
| 3V3 F.Cu track parallel to GATE_N's 45° run, 0.25 mm edge gap | `rule 'Pyro G: gate nets in the pyro block' clearance 0.3000 mm; actual 0.2500 mm` |
| PYRO1_CONT F.Cu track at x 10.9, 0.20 mm from the OUT bar | `rule 'Pyro C: bus, igniter and drain to sense' clearance 0.3000 mm; actual 0.2000 mm` |

The other 201 reports on the copy were:
- 199 `lib_footprint_issues`: the copy had no `kilib`;
- the seeds' own GND-fill shorts;
- the seeds' dangling ends.

**Rule-H seeded suite** (this run's `seed.json`, bound to `fc3d5b34…`, no issues):
- pairs Q124.5–R129.2 (F.Cu, 1.225 mm), R132.1–C129.1 (F.Cu, 1.758 mm) and R177.1–R124.2 (B.Cu, 2.054 mm);
- each seeded at 0.95 mm in eight variants: seed, pad override, minimum lowered, rule deleted, moved first, narrowed,
  RAW_ACT dropped, ACT_GATE dropped;
- each variant caught by DRC, check_actuators, LC-1 and/or pyro_probe;
- control DRC hits 0 for all three pairs.

## 2. Arming break (AGENTS §2.1, §2.2; F7, F8)

**Netlist** (`8b0e04ea…`, Measured):
- PYRO1_BUS = {J124.1, R132.1, R134.2}; PYRO1_IGN = {J121.2, R134.1}; PYRO1_OUT = {C128.1, J121.1, Q124.5, R131.1,
  R173.1}.
- J124.2 is RAW_ACT: Q121's drain, after the actuator switch, which ACT_EN gates from RAW_PROTECTED (R122 / R123).
- No test pad is on BUS, IGN, OUT or any sense node. The test pads on these chains are:
  - TP120 (RAW_ACT, before the link);
  - TP121 (ACT_GATE);
  - TP122 (PYRO1_GATE).

**The only current path into the bus that bypasses J124 is the H-1 cold pull-up:** 3V3 → D120 (BAT54A, anode pin 3,
cathode pin 1; pin 2 no-connect) → R131 10 kΩ → OUT.
- With the link out and the FET off it sources about 3.0 V / (10 kΩ + 11.2 kΩ ‖ 11.2 kΩ) ≈ 0.19 mA. About half of it
  flows through the igniter to the ARM divider (Calc).
- REQUIREMENTS' no-fire figure is about 20 mA.
- With the link in, D120 is reverse-biased.
- This is R4's reviewed design, unchanged.

**Copper (Measured, own script `rules_indep.py`):**
- RAW_ACT is nearest to BUS / IGN at J124.2–J124.1, 2.480 mm: the terminal's own 5.08 mm pitch less its 2.6 mm pads.
  Rule E (1.0 mm) carries no own-part exemption and holds.
- Leaving J124's own pads out, the nearest is 3.28 mm (J124.2 to the BUS bar).
- The RAW bar (y 86.04) and the BUS bar (y 80.96) are 4.08 mm apart edge to edge. R134.2's pad edge is 3.36 mm from
  the RAW bar.
- On In1 / In2, inside the CH1 parts' hull + 1 mm: GND only (check_r9 P-3, `foreign_nets {}`).
- Inner RAW_ACT / BAT_IN: 4.953 mm in plan view from armed copper (D18 ≥ 2.65; In2 RAW_ACT to R131.1).

## 3. Gates defined off in reset and unpowered (AGENTS §2.4; F6, F8)

**Gate network** (netlist; check_actuators 4 / 4b / 4c pins it):
- U1.3 = PE4 → R126 220 Ω → PYRO1_GATE;
- R127 1 kΩ from GATE_N to GND;
- R128 10 kΩ and C126 220 nF from the gate to source (GND);
- Q124 AON7524.
- U1.2 / U1.4 / U1.5 (and U1.16, U1.32) are no-net sentinels (check_actuators 5).

**Datasheet:** AOS AON7524 Rev 1.1 (October 2023), p. 2, https://www.aosmd.com/res/datasheets/AON7524.pdf
(downloaded this pass):
- VGS(th) 0.4 / 0.8 / 1.2 V min / typ / max (VDS = VGS, ID = 250 µA, 25 °C);
- IGSS ±10 µA at VGS ±10 V;
- RDS(on) ≤ 5.8 mΩ at VGS 2.5 V;
- Crss 65 pF typ.

**Calc:**
- In reset the pins are in analog mode (RM0433 §11.3.1, as R8 cited). R128 then holds the gate within
  10 µA × (10 kΩ ‖ 1.22 kΩ) ≈ 11 mV.
- At link insertion C126 divides the drain step: about 8.4 V × 65 pF / 220 nF ≈ 2.5 mV. That is a few mV even at
  several times Crss.

**Reset-voltage table** (check_r9 P-7, this run): every item outside U1's courtyard whose hard short puts ≥ 0.2 V on
the gate keeps ≥ 0.5 mm:

| Net | Gate side | mm | V in reset |
|---|---|---:|---:|
| U1.2 / U1.4 (no net) | GATE_N track (13.0, 53.35) | 0.412 | 0 |
| QSPI_IO2 (U1.1) | GATE_N track | 0.833 | 3.229 |
| PYRO1_OUT (the C128 branch) | Q124.4 | 0.950 | 3.3 |
| PYRO1_CONT (C127.1) | the gate via (9.125, 61.955) | 1.017 | 0.408 |
| 3V3 (U1.6) | GATE_N track | 1.305 | 3.229 |
| PYRO1_CONT run | GATE_N track (8.72, 57.63) | 2.855 | 0.367 |

The table stops at U1's courtyard by design (P-1b). R9P1-PYRO-01 is about what lies just inside it.

## 4. m3.kicad_dru pyro rules A–H, A2: closest approach (Measured)

pyro_probe (check_r9 P-0, this run) and my own script `rules_indep.py`, which uses `min_gap` but not pyro_probe's
predicates, agree:

| Rule | Min | Closest | Where | Margin |
|---|---:|---:|---|---:|
| A RAW_ACT to gate / sense / COLD / mid | 0.5 | 0.730 | RAW_ACT via (27.45, 57.95) to the ARM1_SENSE lane x 28.53, F.Cu | 0.23 |
| B bus / igniter / drain to gate | 0.5 | 0.820 | Q124.5 to the gate track at x 9.125, F.Cu | 0.32 |
| C bus / igniter / drain to sense | 0.3 | 0.577 | R131.1 to the COLD track and R173.1 to the CONT_MID track (tie) | 0.277 |
| D GND to bus / igniter / drain | 0.5 | 0.751 | R9_GND_F fill to R131.1. Nearest GND track: Q124's source comb, 0.770 mm from the drain land | 0.251 |
| E RAW_ACT to bus / igniter | 1.0 | 2.480 | J124.2–J124.1 (own terminal). Next: 3.28 mm | > 1 |
| F bus / igniter / drain to other live | 0.5 | none within 3 mm | (X2 = 0) | — |
| G gate to other live (P-1b scope) | 0.3 | 0.412 | GATE_N's last 0.2 mm outside U1's courtyard to the no-net U1.2 / U1.4 (D-S5-13, C12) | 0.112 |
| A2 RAW_ACT to RAW_ACT_SENSE | 0.3 | 2.054 | R177.1–R124.2, B.Cu | > 1.7 |
| H live pads to sense / gate pads | 1.0 | 1.225 | Q124.5 to R129.2 | 0.225 |
| H+ (strict) | 1.2 | 1.225 | same pair | 0.025 |
| GS (strict) | 1.2 | 1.680 | R128.1 GATE to C127.1 CONT | 0.48 |
| AG (strict) | 1.2 | 1.334 | R121.1 ACT_GATE to C88.2 GND, B.Cu | 0.134 |

H+'s 0.025 mm is set by the AON7524 land's east tie-bar tab (custom pad 5, x 11.325–11.705, y 64.385–64.815) against
R129.2's west edge (x 12.93). This is the AOS land, as in R4 / R8. It is legal and recorded in R9_VALIDATION C13.

**DRU ordering.** Every rule after H is a non-weakening rule (P-4 lists them):
- the thermal-relief sizing;
- "RAW_ACT pins to pours" (GND only);
- J2's 0.508 mm;
- the bare test pads' 1.0 mm.

The test-pad rule's 1.0 mm is below fill margin E's 1.35 mm, but no BUS or IGN zone or test pad exists. So it cannot
lower E anywhere (Measured: no TP on BUS / IGN; no pyro-net zone).

## 5. Solder-bridge table (P-5; F8, R4 method)

`bridge_table.py` (check_r9 P-5 and `gate_bridges`, this run): 134 exposed pairs under 1.5 mm, 0 forbidden.

The 19 pairs under 1.0 mm are all tolerated classes:
- a sense node or midpoint to GND;
- a gate to GND;
- a midpoint to its own node or drain.

The fires-class list holds only a part's own pads:
- Q124.1/.2/.3/.4 to Q124.5, 0.520 mm (the DFN's pins against its drain land);
- C128.1–C128.2, 0.650 mm;
- U1.1–U1.3, 0.700 mm, and U1.3–U1.6, 1.200 mm (LQFP pitch, a sentinel between).

My own scan (`bare_armed.py`, exposed pads per face, 6 mm reach, Measured):
- No foreign bare pad lies within 6 mm of J124.1 or J121.2 on either face.
- J121.1's only foreign bare pad on the bottom is TP122, 5.201 mm away.
- The drain copper's nearest bare GND pads are C128.2 (2.280 mm from Q124.5) and Q124.3 (3.250 mm from C128.1).
- Hand or selective soldering of the terminals therefore has nothing foreign to bridge to.

## 6. D18, D19, D85 (check_r9 K-power-pyro, strengthened)

| Rule | Limit | Measured | Where |
|---|---|---|---|
| D18 inner RAW_ACT / BAT_IN to armed copper (plan view) | ≥ 2.65 mm | 4.953 mm | R9_RAW_ACT_In2 to R131.1 |
| D85 BAT_IN / ACT_FET_S to bus / igniter / drain (same layer) | ≥ 2.5 mm | none within 3.5 mm | — |
| D19 GATE_N to servo PWM (8 layer pairs) | ≥ 0.5 mm | none within 2.0 mm | — |

The bottom BAT_IN pour (x 19.6–39.2) is about 8 mm from J124.1's bottom ring. The ACT_FET_S pour is farther.

## 7. Owner-adopted rules (owner decision 2)

All hold on this run's check_r9:
- **P-1b:** rule G's DRU condition carries `(A.intersectsArea('PYRO_BLOCK') || !A.intersectsCourtyard('U1'))`; the
  seeded G violation above fires.
- **P-3:** no foreign net in the CH1 hull. The hull bbox is 3.06–27.27 × 55.34–89.56 mm, 586.5 mm².
- **P-7:** the table in §3.
- **The strict pad rules:** §4.
- **LC-1:** 0 overrides. The 16 zone clearances are floors only.
- **The fill margins:** rule D holds at 0.751 mm against a GND pour, instead of R8's 0.501.

## 8. Block purity, exits, vias

- **X2 / X2b:** no net other than the CH1 nets, GND and RAW_ACT within 3 mm of bus, igniter or drain copper, on its own
  layer or in plan view.
  - The nearest foreign net is D120's 3V3 feed, 3.047 mm from R131.1.
  - Next is the no-net D120.2, 3.227 mm away.
- **Exits:**
  - GATE_N 11.97 mm, CONT 14.47 mm, ARM1_SENSE 40.0 mm, all F.Cu with no via;
  - *_MCU lanes 2.86 / 2.12 / 2.24 mm (P-8 ≤ 3.0);
  - one pyro via in all: PYRO1_GATE (9.125, 61.955), GND partner (10.425, 62.45) 1.391 mm away (P-9; AGENTS §3).
- **Vias:** 39 GND vias in PYRO_BLOCK. Their nearest armed copper is R134.2, 0.801 mm. M-6 holds: no bottom part within
  1.0 mm of the pyro via.
- **MCU sides past the 4.7 kΩ:** no copper above the 3.3 V rail within 1.5 mm. USB_LIMITED's trunk through U1's interior
  is exactly 1.500 mm from U1.33 and U1.34 (observation 3).

## 9. Renumbered J121 / J124 (owner decision 2, D-S2-01 … 03, D-S10-09)

- **Board pads** (Measured):

  | Pad | Net | Position | Pad shape |
  |---|---|---|---|
  | J124.1 | BUS | (10.1, 80.96) | square |
  | J124.2 | RAW_ACT | (10.1, 86.04) | round |
  | J121.1 | OUT | (10.1, 70.73) | square |
  | J121.2 | IGN | (10.1, 75.81) | round |

  - Both terminals are at rotation 90, so local −y maps to −x and the entry faces the west edge.
  - check_actuators rule 1 reads nets by pad number and is unchanged.
  - The netlist value fields read "ARM CH1: BUS1 / RAW" and "IGNITER 1: E1- / E1+" (pin 1 / pin 2), matching.
- **Legends** (Measured), drawn by pin (D92 / K-legends OK):

  | Legend | Face | Centre | Note |
  |---|---|---|---|
  | `2:RAW` | top | (8.30, 90.84) | forward of J124 |
  | `1:BUS1` | bottom | (7.60, 78.96) | — |
  | `1:E1-` | top | (8.10, 67.53) | aft of J121 |
  | `2:E1+` | bottom | (8.10, 74.01) | — |
  | `ARM` | top | (4.03, 89.91) | — |
  | `IGN` | top | (3.46, 67.63) | — |
  | `J124 2-FUSE-1: ARM LAST` | bottom | — | matches the renumbering |
  | `J124: 5A FAST / 2S` | bottom | — | — |

  On the top each terminal shows one pin legend, which identifies both of its two positions. The arrows under each body
  point −x.
- **Harness text:** ORDERING §7 names the pads by role and position, matching the board: "J124's RAW pad (pin 2, the
  forward position) → F1 → its BUS1 pad (pin 1, the aft position)", and the IGN pad forward and the OUT pad aft for
  J121.
- **Other records:**
  - FMEA_REDUNDANCY has no position-specific J121 / J124 text; it uses R2 designators and pin roles.
  - The pyro sheet's note was updated (D-S2-07).
  - STATUS and M3_R9 describe the variants by role.
- **JLC placement:** `tools/jlc_corrections.json` `C430601|M3_DB128L_2P_BK_SW` is theta 0, residual 0, through
  PAD_ALIAS.
  - EasyEDA's footprint for C430601 was fetched this pass (easyeda.com component API). Its document-layer wire and screw
    glyphs lie on the footprint's −y side of the pin row (y 2981–2989.5 against pads at y 3000, EasyEDA's y down). That
    agrees with our "wire entry on local −y", so theta 0 keeps the entry at −x (Inference).
  - Its polarity mark sits at maker pin 1's end, which is now our pad 2. See R9P1-PYRO-03.

## 10. Wire room and lead direction (P-11, owner decision 1)

- P-11: both terminals enter from −x, 6.353 mm to the bore wall (≥ 6.25).
- fit_check: J121 / J124 6.4–7.0 mm at 5 mm height. Their height margin is 1.23 mm.
- The two bodies abut end to end: courtyards 4.55–15.85 × 68.16–78.39 and 78.39–88.61.
- J124's courtyard ends 0.25 mm aft of J1's (8.90–31.09 × 88.86–100.14). J1 is green, 4-pin, with its entry forward.
- Seen from aft to forward, the four wire positions are OUT, IGN, BUS and RAW at 5.08 / 5.15 mm pitch on the west face.
  ORDERING §7 tells the harness to keep the igniter and ARM harnesses distinct ("cannot be swapped").

## 11. Coating and leakage (P3; MARGIN_PRESCRIPTION §4.13)

The gate pads that matter for leakage are on PYRO1_GATE, held by R128's 10 kΩ. They are covered by the top-side
pyro-block coat, and TP122 is coated last.

| Bare pyro-gate pad | Nearest bare armed-live pad | mm |
|---|---|---:|
| R126.2 | C128.1 | 2.354 |
| R128.1 | Q124.5 | 2.466 |
| C126.1 | C128.1 | 2.527 |
| Q124.4 | C128.1 | 2.629 |

Q124.4 is also 0.52 mm from its own drain land (the DFN). GATE_N's bare pads (R126.1, R127.1) have no armed-live pad
within 4 mm.

**Two facts the R9 records do not state** (R9P1-PYRO-02, Measured):
- U1.3 (GATE_N, bare, uncoated) is 1.200 mm from U1.6 (3V3) and 0.700 mm from U1.1 (QSPI_IO2).
- The F.Cu and B.Cu GND pours stand 0.151 mm from:
  - the bare pyro-gate pads R126.1/.2, R127.1, R128.1, C126.1 and Q124.4;
  - the actuator-gate pads C120.2, R121.1 and Q121.4;
  - the ACT_DRV pads Q122.3 and R121.2.

  TP122 and TP121 keep 1.001 mm (the test-pad rule). R120.2 keeps 0.933 mm and Q120.4 1.436 mm.

## 12. TP122

TP122 is on the bottom at (7.58, 63.5), 1.5 mm square:
- no via in the pad; R8's A8 is gone;
- its gate via has a GND partner 1.391 mm away;
- no bottom part within 2.0 mm (P-9);
- 1.001 mm to the B.Cu GND fill;
- its nearest bare non-gate pad is J121.1's bottom ring, 5.201 mm away. R164.2 (3V3A) is 5.680 mm away.

ORDERING §5 probes TP122 for the leakage and bootloader gates and coats it last.

## 13. Findings

### R9P1-PYRO-01 (Minor, worth fixing): QSPI_IO2 runs 0.25 mm in front of the PYRO1_GATE_N pin, inside U1's courtyard where no R9 gate rule looks

**Requirement:**
- AGENTS §2.4: gates defined off.
- REQUIREMENTS F8: nothing fires while armed with the MCU idle; P-7's intent.
- FMEA I-2 / H-2: the gate pin surrounded by sentinel pins so that no active signal neighbours it.
- r9_plan §1: "safety holds by geometry".
- The step-5 handoff §4, which set GATE_N's 1.5 mm neighbour rule on the premise that "QSPI and HSE escape inward, as in
  R8".

**Finding (Measured).** QSPI_IO2 leaves U1.1 inward, then runs east across the inner pad ends of U1.2, U1.3 and U1.4:
- U1.3, PYRO1_GATE_N, has its pad at x 12.85–13.15, y 51.25–52.85. U1's mask opening equals the pad (no expansion at
  pad, footprint or board level).
- The QSPI_IO2 F.Cu track, 0.20 mm wide, runs (12.0, 50.9)–(13.9, 50.9).
- It is **0.250 mm** from U1.3's pad, and from U1.2 and U1.4.
- Source: `m3_design/r9_route_imu_baro.py` l.78,
  `('QSPI_IO2', 'F', W, [(12.0, 51.55), (12.0, 50.9), (13.9, 50.9), (13.9, 47.1), …])`.

On R8 (`cc044ea0…`) QSPI_IO2's nearest copper to U1.3 was **0.750 mm**: U1.1's straight inward escape along x 17.0, with
the U1.2 sentinel between. No other non-U1-pin copper is within 1.25 mm of U1.3 on R9:
- U1.6's 3V3 escape, 1.25 mm;
- IMU_INT1, 1.369 mm.

The gap is a 0.25 mm masked web, about 0.35–0.6 mm inside the package outline. The body edge is at y 51.5 from the
footprint's 14 mm body (Inference).

**Why nothing caught it.** Every R9 tool exempts U1's courtyard:
- DRU rule G: `!A.intersectsCourtyard('U1')`, and the pad is inside it.
- pyro_probe `Scope.gate_shape` clips gate copper at the courtyard.
- check_r9 P-7 and `r9_pyro_check.gate_neighbours` look only outside it. The module docstring records "1.64 mm from
  GATE_N outside U1's courtyard".
- `bridge_table.py` sees exposed pad pairs only, and the track is masked.

P-1b's exemption was adopted for "the MCU pin's own escape". QSPI_IO2 is another net passing the pin.

**Consequence (Inference):**
- In reset or unpowered both pins are high-impedance, so a short has no source.
- With the firmware running, PE4 is driven low while the QUADSPI drives IO2. A hard short puts the two push-pull drivers
  in contention near mid-rail.
- The gate then sits at about 1.6 V (R126 / R128 pass 0.978). That is above the AON7524's 1.2 V maximum threshold
  (AOS AON7524 Rev 1.1, p. 2), so Q124 conducts and an armed igniter fires.
- The short needs an etch defect, which JLC's electrical test screens, or a mask defect plus solder under the package.
  That is improbable, hence Minor.
- The plug-out cold test would show the shorted-FET signature only if run with QSPI active.

**Fix:**
1. In `r9_route_imu_baro.py`, move the east run inward to y 50.6: (12.0, 51.55) → (12.0, 50.6) → (13.9, 50.6) →
   (13.9, 47.1). Measured against the board's copper with pcbnew shapes, no board saved:

   | Item | Gap |
   |---|---:|
   | U1.3's pad end | 0.55 mm |
   | GND via (13.2, 50.05) | 0.20 mm |
   | U1.6's 3V3 via (14.5, 50.65) | 0.252 mm |
   | IMU_INT1's via (13.21, 49.15) | 0.34 mm |

   The U1.1 stub stays 0.25 mm from the no-net U1.2, as on R8. Rebuild, so the imu_baro gate, the ground stage refill
   and route_check judge it.
2. Optional, for the owner, to keep it from coming back: extend P-7 / `gate_neighbours` to U1.3's own pad against every
   copper item that is not a U1 pad or GND, at 0.5 mm.
3. R8's 0.75 mm needs the run at y ≤ 50.4. That means moving U4's GND via at (13.2, 50.05) (D-S7-10's knot). It is not
   cheap.

### R9P1-PYRO-02 (Minor, worth fixing, records): the coating / leakage record omits U1's own pins and the GND pours beside bare gate pads

**Requirement:**
- AGENTS §2.5: every figure measured.
- REQUIREMENTS F8: "Exposed gate copper near bus or 3V3 copper is covered by the mandatory local coating (P3)".
- R8's precedent: R8 pass 4 §6 recorded "apart from U1's own pins"; D109 recorded R8P3-PYRO-01's 0.151 mm pour figure
  with an owner option.

**Finding (Measured).** R9_VALIDATION's "Coating and leakage" row (l.107) and ORDERING §5's coating paragraph (l.141)
say: "no bare RAW_ACT or 3V3 pad within 5 mm of any pyro gate pad". That is not true as written:
- U1.3 (PYRO1_GATE_N, bare) is **1.200 mm** from U1.6 (3V3) and **0.700 mm** from U1.1 (QSPI_IO2). The bridge table lists
  both as own-part fires-class pairs.
- U1 lies outside the coat region: PYRO_BLOCK starts at y 54.2, and U1's courtyard ends at y 53.145.
- The claim comes from `requalify_r9.json` `pyro.bare`, which leaves out a part's own pads silently ("U1.3 … 3V3: null").

The records are also silent on the R8P3-PYRO-01 class, which persists:
- The F.Cu / B.Cu GND pours stand **0.151 mm** from the bare pyro-gate pads R126.1/.2, R127.1, R128.1, C126.1 and Q124.4.
- They stand the same from the actuator-gate pads C120.2, R121.1 and Q121.4, and the ACT_DRV pads Q122.3 and R121.2.
- R9's strict AG rule (1.2 mm) and the fill margins cover pads, and rules A–G, only.

Not unsafe (Calc / Inference):
- GATE_N is held by R127's 1 kΩ, so a 3V3 leak must be ≤ about 6.4 kΩ to put 0.4 V on the gate.
- GND beside a pyro gate holds it off.
- GND beside ACT_GATE or ACT_DRV turns the actuator switch on. That is the power-switch-defeat class, which matters only
  if the power switch becomes the pad arming device (FMEA H-6(b)).

**Fix (records only).**
- In R9_VALIDATION's coating row and ORDERING §5, write:

  > apart from U1's own pins: U1.6 (3V3) 1.20 mm and U1.1 (QSPI_IO2) 0.70 mm from U1.3, with the no-net sentinels
  > between; GATE_N is held by R127's 1 kΩ, so U1 is not coated
- Add the 0.151 mm pour figures, and R8 D109's option of a GND fill margin round ACT_GATE / ACT_DRV, to the coating row
  or the deviation list.
- Optionally, make `pyro.bare` print own-part pads.

### R9P1-PYRO-03 (Minor, worth fixing, order documents): JLC's pin-1 mark for J121 / J124 now falls on the pad opposite our square pin-1 pad, and ORDERING does not warn JLC

**Requirement:**
- Owner decision 1 / P-11: pyro leads west.
- ORDERING §4: orientation and the expected DFM queries.
- D-S2-08.

**Finding.** EasyEDA's footprint for C430601 (`CONN-TH_2P-P5.08_DB128L-5.08-2P-BK-S`, fetched this pass):
- two round pads, `PAD~ELLIPSE~3980~3000~…~1` and `PAD~ELLIPSE~4000~3000~…~2`;
- a polarity circle on layer 101, `CIRCLE~3969.9999~3020.0787~0.1181~0.2362~101~gge226`, at maker pin 1's end.

With PAD_ALIAS (ours 1 → maker 2) and theta 0, maker pin 1 lands on **our pad 2**: round, RAW at J124 and IGN at J121.
Our square pin-1 pad (BUS / OUT) is at the other end. On R8's base footprint the two coincided.
- The CPL itself is right (§9).
- An operator who lines JLC's dot up with the board's square pad would turn the body 180°. The entry face would then sit
  at x 15.45, against R134's courtyard (x ≥ 15.96) and D120 (Measured positions).
- The terminal would be unusable and reworked inside the coated pyro block. Whether JLC's review does this is an
  Inference.
- ORDERING §4 asks for a 3D-preview check that the entries face x = 0, but lists no expected query for this mismatch.
- J122's mirrored variant has the same mismatch. It is harmless there: unkeyed, symmetric square pins.

**Fix.** Add to ORDERING §4's "Expected DFM queries":

> J121 / J124 (C430601) and J122 (C32713291): JLC's pin-1 mark lands on our pad 2 / pad 10 by design (mirrored
> numbering, R9_DECISIONS D-S2-01 / D-S2-08). Keep the CPL rotation; the J121 / J124 wire entries face X = 0.

## 14. Observations (no finding)

1. **Bridge-table scope** (gate integrity, not this board).
   - `r9_pyro_check.fires_class()` counts only consequences starting "FIRES" or containing "BYPASSES".
   - "Foreign net on armed copper" covers 3V3 or a driven logic line on the drain. FMEA_REDUNDANCY §4.1 shows that class
     firing, yet it is held at bridge_table's 1.0 mm, not the step's 1.5 mm.
   - Moot on R9: X2 = 0 within 3 mm, and no foreign bare pad is within 6 mm of the bus or igniter pads.
2. **The R9 G exception (C12)** is against no-net sentinels (0 V, "no consequence"). Its acceptance is the owner's
   deviation list; it is not a safety gap.
3. **`gate_sense`'s HIGH set** has VBUS but not USB_LIMITED, a 5 V rail. USB_LIMITED's F.Cu trunk inside U1 is exactly
   1.500 mm from U1.33 / U1.34 (ARM1_SENSE_MCU / RAW_ACT_SENSE_MCU), so the record holds, at its boundary.
   RAW_ACT_SENSE_MCU is not in `gate_sense`'s list.
4. **The pyro sheet note** "PE3 (pin 2) and PE6 (pin 5) are sentinels" omits PE5 (pin 4, U1.3's other neighbour) and
   U1.16 / U1.32. check_actuators 5 holds all five as sentinels.
   - The text dates from R6.
   - The binding note covers the firmware: every NC pin is "analog or driven low for sentinels".
5. **`2:RAW` sits between J124 and J1.**
   - Its box (x 7.45–9.15, y 88.50–93.18) touches J1's body outline at x 9.15 and lies 0.25 mm inside J1's courtyard,
     directly above the `J1` designator.
   - It owns J124.2 by 0.81 mm under D92's test, and `ARM` stands beside it.
   - A human-factors note only. Pin 4 is J1's west pin, so the legend cannot read as J1's pin 2 by position.
6. **Owner decision 1 reads "battery leads the east edge".**
   - J1 enters from the forward edge and spans x 8.9–31.1, its courtyard 0.25 mm forward of J124's.
   - D-S1-16 records the reading "battery leads east to J1's forward entry".
   - The pyro and battery leads still leave by different edges. Passed to the requirements reviewer.
7. **The BAT_ENABLE latch class** (R8 "Pyro review observations") is smaller on R9. BAT_ENABLE's nearest copper:

   | Net | mm | Where |
   |---|---:|---|
   | BAT_IN | 0.200 | U9's own pin pitch |
   | RAW_PROTECTED | 0.300 | — |
   | BAT_SW_SOURCE | 0.708 | J1.3's pad |
   | armed, ACT_EN, ACT_DRV | > 1 mm | — |

   R8 had 0.70 mm to R134 and 0.40 mm to Q122.
8. **Plate strain** at 100 g quasi-static (this run's `plate.json`): J121 780 and J124 840 µε. R8 had 899 / 799 on its
   own supports (`sources/r8_design/step9/evidence/plate_r8.json`). The west edge carries the CH1 column with no mid
   support, but the strain is comparable to R8's.

## 15. Scratch

Measurement scripts and their text outputs stay in the session scratchpad `r9review/pyro/`:
- `scripts/`: `dump_ch1.py`, `neigh.py`, `rules_indep.py`, `bare_armed.py`, `run_step5_fns.py`, `u1pins.py`,
  `u1pins_r8.py`, `u1corner.py`, `qspi_gap.py`, `qspi_fix.py`, `batenable.py`, `mcu_high.py`, `actgnd.py`,
  `block_parts.py`, `silk.py`, `silk2.py`, `q124.py`, `seed.py`;
- `gate/`: this run's check.sh reports.

The R8 board copy, the seeded copy and the temporary folders are deleted.
