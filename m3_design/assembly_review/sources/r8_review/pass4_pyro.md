# R8 review pass 4: pyro and arming safety

Reviewer: independent, read-only. No repository file changed except this report, and the board and schematic were never
saved. Board `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`c84f00b88f5fb9409de40f33b2d51a48fb29fb66c386c869b7f93ea791e37c54`, confirmed before and after the review.
`git status --short` was identical before and after. The netlist `schematic.net.xml` is `0cc1ed692fb99dd2…`, unchanged
since pass 2.

Comparison boards, extracted read-only into the session scratchpad `p4pyro/`:
- Pass 3's board `990c8040…`, rebuilt from the coordinator's backup `r8_backup_990c8040/tracked.diff` on top of
  `431025d`. Its SHA-256 matched.
- R7 `c872a3d3…`, from `git show 431025d:…`.

Both copies are deleted. `../rocket-flight-computer-r7` and `-r6` were not touched.

**Verdict: 0 Critical, 0 Major, 1 Minor.** The Minor concerns the records and a survey tool. It needs no board change.

**Previous findings.** Both pass-3 findings in this dimension are closed in the records:
- R8P3-PYRO-01 (the ACT_GATE pour figures);
- R8P3-PYRO-02 (R81.2 in the GND row).

**What fix pass 3 changed near pyro copper:**
- No copper within 3 mm of armed copper.
- No pyro gate or sense copper. RAW_ACT_SENSE (PB0's sense, rules A2 and H) moved 0.05 mm east with R172; it is not a
  pyro net.
- R165's BAT_ENABLE via went from 0.6 mm to 0.5 mm. That only widens its gaps.

I re-ran every pass-3 neighbour measurement on both boards. Fourteen of the fifteen outputs are byte-identical:
rule margins, armed / plan / bare-armed neighbours, gate, bare-gate, battery bypass, D18, D19, inner rasters with A8,
drain neighbours, GND vias, bare GND pads, the actuator gate against GND, barrels and holes, and the block via count.
The fifteenth (sense) differs only at USB_LIMITED / R172.

**Gate and pinned contract:**
- `tools/check.sh` exits 0.
- The seeded DRC fires rules A2, D, E, F and G.
- `m3.kicad_dru`, `check_actuators.py`, `m3.kicad_pro` and the three pyro / actuator / battery sheets are unchanged.
- The pins hold: DRU_SHA `1674d58b…` and CHECK_ACTUATORS_SHA `5de1eb3c…`.

**The new Minor (R8P4-PYRO-01).** Rule G ("gate nets in the pyro block", 0.3 mm) is missing from:
- `step9/requalify.py`'s rule table;
- M3_R8's "closest approach per pyro rule" table.

Both claim to cover every rule. G is the one pyro rule whose closest copper sits exactly at its minimum: 0.300 mm, the
GATE_N lane to the CONT lane. That makes R8_VALIDATION's "every rule's closest approach listed" untrue.

Labels:
- **Measured:** pcbnew on the boards above. The scripts are in the session scratchpad `p4pyro/`: pass 3's `measure.py`,
  `rules.py`, `d18.py`, `under.py`, `outn.py`, `gndvias.py`, `refill.py`, `diffboards.py`, `barrels.py`, `baregnd.py`,
  `actgnd.py`, `blockvias2.py`, re-run unchanged through `runall.sh`, plus this pass's `vianb.py`, `l10via.py`,
  `baregnd2.py`, `rulesG.py`, `seed.py` and `seed2.py`.
- **Datasheet:** a cited maker document.
- **Inference:** reasoning that was not measured (AGENTS §2.5).

## 0. Previous findings in this dimension (pass 3, board `990c8040…`)

**R8P3-PYRO-01** (Minor, not worth fixing): the R120.2 GND via is not ACT_GATE's nearest GND copper.
- **Disposition:** closed in the records (D109): the 0.151 mm pour figure, the candidate closed, a GND-to-gate zone rule
  left as an owner option.
- **Verified on `c84f00b8…`:**
  - `actgnd.py` is byte-identical to pass 3. GND_B / GND_F stand 0.151 mm from R120.2, C120.2, R121.1, R121.2 and
    Q122.3; the via (15.0, 107.3) is 0.180 mm from R120.2.
  - No bare GND pad is within 1.3 mm of any ACT_GATE / ACT_DRV pad (`baregnd2.py`), so the records' "no GND pad within
    1.0 mm" holds.
  - The text is updated in R8_VALIDATION's ACT_GATE row, C12 and C12b, M3_R8's coating section (l.385–396), D109 and
    `fix2_handoff.md` l.61–65. The handoff says "0.150 mm" where the board measures 0.151 mm (§8).
- **Status:** closed.

**R8P3-PYRO-02** (Minor, worth fixing, records): R81.2 is missing from the GND row.
- **Disposition:** R8_VALIDATION's pyro observations (GND row and closing sentence) and M3_R8.
- **Verified on `c84f00b8…`:**
  - The GND row names R81.2 at 1.825 mm from J121.1, the drain's nearest bare GND pad (pass 2's board: R83.2 2.205 mm;
    R7: U7.8 1.630 mm), with L10 met (courtyard 1.58 mm).
  - The closing sentence reads "R81.1 (BAT_ENABLE) and R81.2 (GND)–J121.1 1.825 mm".
  - M3_R8 l.400–403 says the same.
  - Re-measured: `baregnd.py` gives J121.1–R81.2 1.825 mm on B.Cu, unchanged.
- **Status:** closed.

**Pass 1 and pass 2 items** (R8P1-PYRO-01…04, R8P2-PYRO-01…04): as pass 3 found. Re-measured on `c84f00b8…`:
- ACT_FET_S to J124.1: 1.089 mm.
- RAW_ACT to R127.1: 1.115 mm.
- GATE_N lane to the CONT lane: 0.300 mm.
- ACT_GATE stub to C120.1: 0.264 mm.
- The drain's nearest battery copper: 3.562 mm.
- `battery_pyro` and `test_r8_check`: 23 tests OK.
- Binding constraint 12 (the PE4 bootloader step, numbered 11 in pass 3) is present and bound to `c84f00b8…` (§3).

Status: closed or dispositioned.

## 1. Gate runs (this pass)

**`tools/check.sh`** (unchanged board), exit 0:
- DRC 0 violations, 0 unconnected, parity 0, ERC 0;
- metadata / 3D audit OK; silkscreen 0;
- `R8 CAD contract: OK`;
- route_check r8: 0 failing, 3 allowlisted, 0 stale, 0 out-of-date no-GND reasons (22 bump windows);
- `actuator safety contract: OK`;
- fit OK (J121 / J124 1.15 mm, wire room 6.3–6.9 mm).

**check_r8 evidence** (`--report` to scratch):
- `battery_pyro`: nearest 1.089 mm (ACT_FET_S zone to J124.1, B.Cu).
- `inner_power_pyro`: 2.65 mm (BAT_IN In2 to R134.1).
- `gate_servo`: nothing under the limit on 8 layer pairs.
- `inner_signal`: In2_rigid_exempt 3.4 mm.
- `notes`: empty.

**`tools/test_r8_check.py`:** 23 tests OK.

**Seeded DRC**, on two scratch copies with `m3.kicad_pro` / `m3.kicad_dru`, `kicad-cli pcb drc --severity-all`, copies
deleted. KiCad loads the custom rules and they fire:

| Seed | DRC result |
|---|---|
| RAW_ACT F.Cu track 0.75 mm from J124.1 | `rule 'Pyro E: RAW_ACT to bus and igniter (ARM break)' clearance 1.0000 mm; actual 0.7500 mm` |
| BAT_ENABLE F.Cu track 0.40 mm from J121.1 | `rule 'Pyro F: …' clearance 0.5000 mm; actual 0.4000 mm` |
| RAW_ACT_SENSE B.Cu track 0.25 mm from a RAW_ACT track | `rule 'Pyro A2: …' 0.3000; actual 0.2500` |
| Via on J121.2's IGN track | `rule 'Pyro D: GND to bus, igniter and drain'` against all four GND pours |
| B.Cu track 0.25 mm from the GATE_N lane | `rule 'Pyro G: gate nets in the pyro block' 0.3000; actual 0.2500` |

Two seeds took a different net when KiCad's connectivity merged them with the copper they landed on: the D via became
PYRO1_IGN and the G track became PYRO1_CONT. Rules D and G still fired.

The first E seed, on B.Cu inside the GND_B pour, reported only its 0.000 mm GND short and A2, not rule E. Re-seeded on
F.Cu, rule E fired.

**Pinned files** (SHA-256 against the fix-3 baseline):
- Unchanged since pass 3: `m3.kicad_dru` `1674d58b…` (= `check_actuators.DRU_SHA`), `check_actuators.py` `5de1eb3c…`
  (= `check_r8.CHECK_ACTUATORS_SHA`), `m3.kicad_pro` `3730b060…`, `tools/check_r8.py` and every schematic.
- `git diff 431025d` of `pyro.kicad_sch`, `actuator_power.kicad_sch` and `battery_entry.kicad_sch` shows only
  `(rev "M3-ASSY-R8")`.

**Zone fills:** a native `ZONE_FILLER` refill in memory reproduces the saved fills: 14 zone / layer sets, 0 differences.

## 2. What fix pass 3 changed, and its reach

`diffboards.py` on `990c8040…` → `c84f00b8…` finds these changes, and no zone outline changed:
- **Tracks:** USB_LIMITED's trunk y 37.25 → 37.3 (5 segments); CAM_PWR_EN's lower leg (3 segments); RAW_ACT_SENSE
  x 30.6 → 30.65 (2 segments) and RAW_ACT_SENSE_MCU's stub to R172.2.
- **Vias:**
  - BAT_ENABLE (16.6, 104.5): 0.6 → 0.5 mm, same position and drill;
  - GND (28.875, 32.875) → (29.125, 32.625).
- **Footprint:** R172 (30.6, 48.1) → (30.65, 48.1), bottom.

Reach of each change:
- **Armed copper** (PYRO1_BUS / IGN / OUT): nothing within 3 mm changed. `out_armed`, `out_armed_plan`,
  `out_bare_armed`, `out_outn`, `out_gndvias`, `out_baregnd`, `out_barrels` and `out_bypass` are byte-identical to pass
  3's board. `fix3_pyro_neighbours_r8.json` equals fix pass 2's, 0 differences outside the SHA. `fix3_requalify_r8.json`
  differs only in ARM1_SENSE_MCU's nearest-copper coordinate (the USB_LIMITED trunk's new y).
- **Pyro gate / sense copper:** `out_gate` and `out_bare_gate` are identical. `out_sense` differs only at
  USB_LIMITED / R172:
  - R172.1 / R172.2 to USB_LIMITED: 0.180 → 0.230 mm (bare pads, now farther);
  - new: the RAW_ACT_SENSE lane at (30.65, 48.53–57.45) is exactly 0.200 mm from USB_LIMITED's hop via (31.25, 55.3),
    masked track to tented via, as D106 records.

  A bridge there puts 5 V on PB0's divider node, behind R172's 4.7 kΩ, about 0.3 mA (Inference). RAW_ACT_SENSE then
  reads RAW_ACT live while it is dead. That is a false "armed" reading under arming option H-6(b) (FMEA_REDUNDANCY l.47)
  with no energy behind it, so it cannot fire (Inference). The pair it replaces (bare R172 pads at 0.180 mm) was closer.
- **R165's BAT_ENABLE via** (`vianb.py`, both boards). It is inside PYRO_BLOCK, at the actuator switch, not the pyro
  channel. No pyro net lies within 1.5 mm of it on any layer.

  | Layer | Neighbour | `990c8040…` | `c84f00b8…` |
  |---|---|---:|---:|
  | B.Cu | Q120.9 (bare BAT_IN) | 0.180 | 0.230 |
  | B.Cu | GND_B | 0.467 | 0.519 |
  | F.Cu | R8_BAT_IN_F | 0.333 | 0.383 |
  | F.Cu | GND_F (refilled) | 0.151 | 0.151 |
  | In1 | BAT_IN via (17.7, 105.6) | 0.956 | 1.006 |
  | In2 | R8_BAT_IN_In2 | 0.301 | 0.301 (refilled) |

  The latch class is unchanged in kind and smaller in exposure.
- **R5 L10 exceptions at the MCU-side pyro vias** (`l10via.py`, 5 µm steps):
  - ARM1_SENSE_MCU (29.3, 47.5): R170 0.64, R172 0.69, C15 0.84 mm;
  - PYRO1_CONT_MCU (24.0, 53.7): R168 0.24 mm.

  These match `L10_EXCEPT`: R172 0.685 after D106, the others unchanged.
- **CAM_PWR_EN and the GND cover via** sit at y 27–37, far outside every pyro neighbour list.

## 3. Arming break and gate defined off (AGENTS §2.1, §2.2, §2.4; F6, F8, F10)

**Netlist** (`0cc1ed69…`):
- PYRO1_BUS = {J124.1, R132.1, R134.2}; PYRO1_IGN = {J121.2, R134.1}; PYRO1_OUT = {C128.1, J121.1, Q124.5, R131.1,
  R173.1}.
- J124.2 is RAW_ACT, Q121's drain, after the actuator switch.
- No test point is on BUS, IGN or OUT. The test points on these chains are TP120 (RAW_ACT, before the link), TP121
  (ACT_GATE) and TP122 (PYRO1_GATE).

**Copper:**
- Rule E's closest is 1.300 mm (RAW_ACT F.Cu / B.Cu pours to J124.1).
- Battery-live copper is ≥ 1.089 mm from BUS / IGN on the same layer; on the drain it is 3.562 mm.
- On In1 / In2 the barrels see only GND at 0.501 mm and the other pin of the same terminal at 2.48 mm.
- In plan view, the B.Cu BAT_IN pour is 0.950 mm from R134's F.Cu pads, with the full 1.6 mm stack and In1 / In2 GND
  between (as pass 3).

**Gate network** (unchanged; check_actuators 4 / 4b / 4c / 16):
- R126 220 Ω series; R127 1 kΩ to GND at the MCU side; R128 10 kΩ and C126 220 nF gate to source; AON7524 pinned
  C431195.
- U1.3 = PE4. Its neighbours U1.2 / U1.4 / U1.5 are no-net sentinels.
- AON7524 V_GS(th) is 0.4 V minimum and I_GSS ±10 µA (AOS AON7524 datasheet p. 2,
  https://www.aosmd.com/res/datasheets/AON7524.pdf). R127 holds the gate off in reset and unpowered (Inference: about
  11 mV from I_GSS).

**Bootloader** (fix pass 3, R8P3-RF-01 / R8P3-REQUIREMENTS-01). Binding note constraint 12 (`r8_binding_note.json`, bound
to `c84f00b8…` / `0cc1ed69…`), D6.8, F10, M3_R8 and ORDERING §5 l.161 all give the same order:
1. PE4 low;
2. the SX1262 asleep, then PE9 low;
3. last, GPIOE reset through RCC_AHB4RSTR, or PE4 kept low with PE9 returned to analog.

PE4 is low from step 1 to the bootloader, and the GPIOE reset only makes it analog with R127 holding the gate off. So the
reordering keeps the gate off at every point (Inference; GPIOx_LCKR is cleared by a peripheral reset, RM0433 §11.4.8).

ORDERING l.161's new bench check:
- reads TP122 below 0.1 V in the bootloader with the ARM link out, before USB is unplugged;
- then runs the armed static gate there, with USB unplugged per l.150's armed-step rule.

The "bootloader keeps running" Inference is plausible: U11 (TPS2121) takes USB_LIMITED on IN1 and RAW_PROTECTED on IN2
with PR1 tied to GND, so with the bench supply on, VLOGIC should not switch source when USB is removed (Inference from the
netlist; see §8).

## 4. `m3.kicad_dru` pyro rules and the check_actuators contract

The DRU is R7's, unchanged and pinned. Nothing after rule H lowers a pyro clearance: the small-pad thermal rule sets no
clearance, "RAW_ACT pins to pours" is GND only, and J2's 0.508 mm is above rule D. Closest approach per rule
(`rules.py`; conditions transcribed from the DRU and re-checked against the file):

| Rule | Min | Pass 4 closest | Where | Pass 3 |
|---|---:|---:|---|---:|
| A RAW_ACT to gate / sense / mid | 0.5 | 0.501 | RAW_ACT B.Cu box to the CONT lane; F.Cu pour to C127.1 | 0.501 |
| B bus / igniter / drain to gate | 0.5 | 0.670 | Q124.5 to the PYRO1_GATE track | 0.670 |
| C bus / igniter / drain to sense | 0.3 | 0.377 | PYRO1_BUS track to R132.2 | 0.377 |
| D GND to bus / igniter / drain | 0.5 | 0.501 | GND_B to J124.1, J121.1, J121.2 | 0.501 |
| E RAW_ACT to bus / igniter | 1.0 | 1.300 | RAW_ACT F.Cu / B.Cu pours to J124.1 | 1.300 |
| F bus / igniter / drain to other live | 0.5 | 0.700 | BAT_ENABLE track to R134.1 / R134.2 | 0.700 |
| G gate in the block to other live | 0.3 | **0.300** | GATE_N lane x 18.75 to the CONT lane x 19.25, B.Cu (R7: 0.316, GATE_N to SERVO2_MCU on In2) | 0.300 |
| A2 RAW_ACT to RAW_ACT_SENSE | 0.3 | none within 2.0 mm | | none |
| H live pads to sense / gate pads | 1.0 | 1.025 | Q124.5 to R129.2 | 1.025 |

**check_actuators** passes on the board: rule texts, minima, nets, per-rule hashes, PYRO_BLOCK, pinned parts and
ACT_NETS. The 40 GND vias in PYRO_BLOCK and the nearest armed-live 0.522 mm (J121.2) are unchanged.

**The rule-G gap in the records:**
- `step9/requalify.py`'s `RULES` (l.49–63) has entries for A, B, C, D, E, F, A2 and H, but no G, although its docstring
  (l.8) says "per m3.kicad_dru pyro rule (A-H, A2)".
- `fix3_requalify_r8.json`'s `pyro_rules` therefore has 8 entries.
- M3_R8's table (l.322–331, "Closest approach per pyro rule") lists the same 8, also without G.

That gap is R8P4-PYRO-01.

## 5. D18, D19, the barrels and holes

- **D18:** `d18.py` is byte-identical to pass 3.
  - BAT_IN In2 is 2.650 mm from R134.1; the ACT_GATE via 2.790; the BAT_ENABLE via (40.42, 93.5) 3.178; RAW_ACT In2
    west 3.260 mm.
  - Pyro-family items: the D70 ARM1_SENSE In2 link (under the BUS track, In1 GND between), the CONT exit via 0.715 and
    the TP122 via 1.250 mm.
  - Met.
- **D19:** GATE_N's nearest servo copper is 5.890 mm (B.Cu lane to J122.1) on every layer pair. Met.
- **Barrels and holes** (`barrels.py`, identical):
  - J124.1's non-GND neighbours: ACT_FET_S 1.089, RAW_ACT 1.300, ACT_GATE via 2.521 and ARM1_SENSE via 2.974 mm.
  - J121.1's: R81.1 1.825 and R82.2 1.922 mm.
  - J121.2's: the BAT_ENABLE track 1.190 and RAW_PROTECTED 2.465 mm.
  - Pyro / RAW_ACT holes are ≥ 1.009 mm wall to wall from foreign holes (the GATE_N via to the GND via (22.85, 89.63)).

## 6. Coating, leakage and A8

- Bare pyro-gate copper to bare bus / igniter copper: 1.027 mm (R126.2–R134.2) and 1.491 mm (C126.1–R134.1), the rigid
  block.
- No bare 3V3 / RAW_ACT / always-live pad lies within 5 mm of a pyro gate pad, apart from U1's own pins: U1.3 to U1.6
  (3V3) is 1.200 mm and to U1.1 0.700 mm, R7's MCU pin geometry with the sentinels between. `out_bare_gate` is
  identical to pass 3.
- **A8** (`under.py`, identical):
  - TP122 at (20.45, 92.4), bottom, Ø1.5 mm; its 0.6 / 0.3 mm via is at the centre, hole edge 0.60 mm inside the pad
    edge.
  - Nearest GND vias: 2.717, 3.665 and 3.761 mm. Nearest foreign copper: 1.001 mm (GND_B).
  - route_check: 0 out-of-date no-GND reasons.
- The inner layers under every CH1 pad (+0.5 mm, 0.1 mm grid) carry only GND, voids, the pad's own net and block
  vias.
- ORDERING §5's coating order is unchanged and still covers the block: TP122 last, then the static gate, J2 after the
  last SWD session. The new bootloader check reads TP122 before coating, in the bench-acceptance phase.

## 7. Findings

### R8P4-PYRO-01 (Minor, worth fixing, records and tool): rule G is missing from `requalify.py` and from M3_R8's per-rule table

- **Requirement:**
  - AGENTS §2.5 and the owner's acceptance of the records: every figure that is claimed must be measured.
  - R8_VALIDATION l.132 ("Pyro exits and rule margins | Closed | every rule's closest approach listed").
  - M3_R8 l.319 ("Closest approach per pyro rule").
  - `requalify.py` l.8 ("per m3.kicad_dru pyro rule (A-H, A2)").
- **Finding:**
  - `requalify.py`'s `RULES` dict covers A, B, C, D, E, F, A2 and H. Rule G ("Pyro G: gate nets in the pyro block",
    0.3 mm, the only area-conditioned pyro rule, `A.intersectsArea('PYRO_BLOCK')`) has no entry. The fix-3 evidence
    `fix3_requalify_r8.json` and M3_R8's table, built from it, list 8 of the DRU's 9 pyro rules.
  - G is the one rule whose routed copper sits exactly at its minimum. The PYRO1_GATE_N lane (x 18.75, w 0.2,
    (18.75, 87.78)–(18.75, 54.30)) runs 0.300 mm from the PYRO1_CONT lane (x 19.25) on B.Cu. The whole 33.5 mm GATE_N
    segment is governed by G because it intersects PYRO_BLOCK (y ≥ 84). R7's G closest was 0.316 mm.
  - The figure is in the records elsewhere: M3_R8's exits table ("PYRO1_GATE_N 0.30 mm"), R8P1-PYRO-04 (the
    hard-short gate near 0.37 V) and ORDERING's warm static gate. So nothing is unscreened.
  - But the rule-by-rule table, which the owner reads as complete, omits the zero-margin rule. The tool that
    re-qualifies the margins after each copper change would not see a G regression either. DRC still would (seeded G
    fires, §1).
  - No board defect.
- **Evidence (Measured):**
  - `rules.py` on `c84f00b8…`:
    `Rule G (min 0.3): 0.300 PYRO1_GATE_N trk(18.75,87.78)-(18.75,54.30) w0.20 / PYRO1_CONT trk(19.25,87.00)-(19.25,58.10) w0.20 B.Cu`.
  - `rulesG.py` on R7 `c872a3d3…`:
    `0.316 PYRO1_GATE_N trk(23.00,86.03)-(30.20,86.03) w0.20 / SERVO2_MCU trk(33.70,83.22)-(29.05,87.87) w0.15 In2.Cu`.
  - `python3 -c` over `fix3_requalify_r8.json['pyro_rules']`: keys A, B, C, D, E, F, A2 and H only.
  - `requalify.py` l.49–63.
  - M3_R8 l.322–331.
- **Fix** (records and tool, no board change):
  1. Add G to `requalify.py`'s `RULES`. The predicate: a in GATES, the item intersects PYRO_BLOCK (x 4–42, y 84–114.4),
     b not in GND / RAW_ACT / LIVE / GATES, with Q124's own pads exempt. This needs one area test beside the net
     predicate.
  2. Re-run `requalify.py` into the evidence.
  3. Add the row "G gate nets in the block to other live | 0.3 | 0.300 | GATE_N lane (x 18.75) to the PYRO1_CONT lane
     (x 19.25), B.Cu, parallel from y 87.0 to 58.1 (R8P1-PYRO-04) | 0.316 (GATE_N to SERVO2_MCU, In2)" to M3_R8's table.
  4. Keep R8_VALIDATION l.132's "every rule" claim, which is then true.

## 8. Observations (no finding)

**Records checked against the board, all exact:**
- M3_R8's 7 nets within 3 mm of armed copper (BAT_ENABLE 0.700, ACT_FET_S 1.089, RAW_ACT 1.300, BAT_OVLO 1.922,
  RAW_PROTECTED 1.975, BAT_DAMP 2.450, ACT_GATE via 2.521 mm).
- 40 GND vias in PYRO_BLOCK, the nearest armed-live 0.522 mm.
- D18 2.65 mm; the drain's battery copper 3.562 mm.
- The BAT_ENABLE row:
  - 0.216 mm to bare R175.2;
  - 0.40 mm to Q122.1 / .3;
  - 0.70 mm to R134;
  - the via 0.23 mm from Q120.9;
  - the nearest BAT_IN copper U9.1–U9.5 at 0.200 mm.
- A2: no RAW_ACT_SENSE copper within 2.0 mm of RAW_ACT; the records say "none within 1.3 mm".

**Small wording mismatch:** `fix2_handoff.md` l.63's fix-pass-3 annotation says the pours stand "0.150 mm" from the five
ACT_GATE / ACT_DRV pads. R8_VALIDATION, M3_R8 and D109 say 0.151 mm, which is what the board measures. This is cosmetic.

**The bootloader static gate.** ORDERING l.161 runs it "with USB unplugged after the jump (the bootloader keeps running
on the bench supply, Inference)". The direct proof that PE4 is low in the bootloader is the TP122 reading taken just
before, with USB still connected. If the board ever reset on the unplug, the static gate would silently run in the
application and still pass. U11's wiring (IN2 = RAW_PROTECTED, PR1 to GND) makes a source switch on USB removal
unlikely (Inference, not checked against TI's TPS2121 datasheet in this pass). A one-line "afterwards, re-plug USB and
confirm the DFU device is still present without a new jump" would close it. This is optional, so it is not raised.

**Rule-G-class pairs and the GATE_N via:** the 0.300 mm GATE_N–CONT lane and the GATE_N via's 0.220 mm to the
ARM1_SENSE lane are unchanged. They stay R8P1-PYRO-04's disposition (hard short: the gate near 0.37 V in reset against
the 0.4 V minimum threshold; the static gate repeated warm).

**Scratch:** the comparison boards and seeded copies are deleted. Only small scripts and text outputs remain in
`p4pyro/`.
