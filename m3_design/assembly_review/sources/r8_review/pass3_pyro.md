# R8 review pass 3: pyro and arming safety

Reviewer: independent, read-only (no repository file changed but this report; the board and schematic were never saved).
Board `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `990c8040c5b8457bd2bd1717ed3e5c2725f32c1dda1cd7f826a0c2b458d28b18`
(confirmed before and after the review; `git status --short` identical before and after). Netlist `schematic.net.xml`
`0cc1ed692fb99dd2…` (unchanged since pass 2). Comparison boards, extracted read-only into the session scratchpad
`p3pyro/`: pass 2's board `6600ef94…` (from fix pass 2's `pre_fix2_state.tgz`) and R7 `c872a3d3…`
(`git show 431025d:…`). `../rocket-flight-computer-r7` and `-r6` were not touched.

**Verdict: 0 Critical, 0 Major, 2 Minor.** Both Minors are about the records; neither needs a board change. Every
pass-2 finding in this dimension is closed or properly dispositioned. PYRO-01's drain case kills the old-ARM_SIDE mutant
(re-run here).

The arming break is complete in the netlist and in copper. The gate is defined off in reset and unpowered. Every
`m3.kicad_dru` pyro rule is loaded: seeded DRC on a scratch copy fails rules D, E and F, and `battery_pyro` catches the
drain. Every rule is met with the same closest approach as pass 2. `check_actuators` holds. D18 is 2.65 mm and D19
5.89 mm. Coating / leakage distances and A8 are unchanged.

Fix pass 2 changed only one thing near armed or pyro-control copper: R81's move (D100). A copper diff of `6600ef94…` against
`990c8040…` finds the sense, gate and bare-gate neighbour lists identical. Only R81's two pads and one regenerated step-7
GND via moved within 3 mm of armed copper. R81.1 (BAT_ENABLE) went from 2.720 to 1.825 mm from the drain barrel J121.1,
bare to bare; that pair is recorded and fails toward the latch class, not a fire. R81.2 (GND) is now the drain's nearest
bare foreign GND pad at 1.825 mm. It is within R5 L10 and farther than R7's 1.630 mm, but it is missing from the pyro
observations' GND row (R8P3-PYRO-02).

Fix pass 2 left one candidate for pass 3: step 7's GND via 0.180 mm from R120.2 (ACT_GATE). It is not the closest GND
copper to the actuator gate. The GND pours already stand at 0.151 mm from all five bare ACT_GATE / ACT_DRV pads, R120.2
included (R7: four pads, also 0.151 mm). The proposed `make_ground` change would therefore gain nothing (R8P3-PYRO-01).

Labels: **Measured** = pcbnew on the boards above (scripts in the session scratchpad `p3pyro/`: `measure.py`, `rules.py`,
`d18.py`, `under.py`, `outn.py`, `gndvias.py`, `refill.py` (pass 2's, re-run unchanged), and this pass's `diffboards.py`,
`barrels.py`, `baregnd.py`, `actgnd.py`, `blockvias2.py`, `l10.py`, `pos.py`); **Datasheet** = cited maker document;
**Inference** = reasoning not measured (AGENTS §2.5).

## 0. Previous findings in this dimension (pass 2, board `6600ef94…`)

| Pass-2 item | Disposition (R8_VALIDATION "Review pass 2", D103) | Verified on `990c8040…` | Status |
|---|---|---|---|
| R8P2-PYRO-01 `battery_pyro` left out the drain | `check_r8.ARM_SIDE` = BUS / IGN / OUT (l.110), docstring (l.31–37, l.683); seeded drain case in `test_r8_check` l.268–270; D85 / D103, M3_R8 l.318–321, REQUIREMENTS F8, R8_VALIDATION hard-gate row | `test_r8_check` 23 OK. **Mutant re-run:** in a scratch copy of `tools/` with ARM_SIDE reverted to BUS / IGN, the test fails at l.270 (`'from PYRO1_OUT J121.1' not found`). **Seeded on a scratch board copy:** an ACT_FET_S track 0.820 mm from J121.1 gives `battery-live copper near the ARM side: ACT_FET_S track (36.0, 93.0) is 0.820 mm from PYRO1_OUT J121.1 on B.Cu`. On the real board: nearest 1.089 mm (ACT_FET_S–J124.1); the drain's nearest battery copper is 3.562 mm (BAT_IN R82.1–J121.1, bare to bare, B.Cu) | Closed |
| R8P2-PYRO-02 GND beside the drain called "the safe direction" | M3_R8 l.359–368 rewritten; R8_VALIDATION pyro observations gained the GND row (l.491) | Text now says GND "beside the drain PYRO1_OUT … does not [fail safe]", gives the 24 Ω no-fire leak figure (Inference) and both vias (0.528 / 0.537 mm, re-measured identical). No other "safe direction" claim about GND on the drain remains (grep of M3_R8, R8_VALIDATION, STATUS, ORDERING, R8_DECISIONS). The row misses the one new bare GND pad: R8P3-PYRO-02 | Closed (record gap: PYRO-02 here) |
| R8P2-PYRO-03 the bootloader-jump constraint did not put PE4 low | `binding_note.py` constraint 11; `r8_binding_note.json` regenerated; D6 item 8 (R8_DECISIONS l.295–299); REQUIREMENTS F10; M3_R8 l.494–496 | The note binds `990c8040…` / `0cc1ed69…`. Constraint 11 reads "first drive PE4 (PYRO1_GATE_N) low, or reset GPIOE through RCC_AHB4RSTR, which also returns PE4 to analog so R127 holds the gate off". Constraint 6 (lock PE4) and constraint 9 (loader pins) are unchanged. The LCKR reading (freezes MODER / OTYPER / OSPEEDR / PUPDR / AFR, not ODR; cleared by MCU or peripheral reset; RM0433 §11.3.8 / §11.4.8) is the reviewer's reading, as in pass 2, not checked on silicon | Closed |
| R8P2-PYRO-04 ACT_GATE's chamfered stub 0.264 mm from bare C120.1 (fails safe) | Accepted, recorded (R8_VALIDATION l.201, l.394, l.492) | Re-measured 0.264 mm (`trk(10.90,105.56)-(12.50,107.16)` to C120.1) | Properly dispositioned |
| Pass-1 items (R8P1-PYRO-01…04) | as pass 2 found | ACT_FET_S 1.089 mm, RAW_ACT to R127.1 1.115 mm, GATE_N lane 0.300 mm to the CONT lane, all unchanged | Closed / dispositioned |

## 1. Gate runs (this pass)

| Run | Result |
|---|---|
| `tools/check.sh` (unchanged board) | exit 0: DRC 0 / unconnected 0 / parity 0 / ERC 0; audit OK; silk 0; `R8 CAD contract: OK`; route_check r8 0 failing / 3 allowlisted / 0 stale / 0 out-of-date no-GND reasons; `actuator safety contract: OK`; fit OK (J121 / J124 1.15 mm, wire room 6.3–6.9 mm) |
| check_r8 evidence (`r8.json`) | `battery_pyro` nearest 1.089 mm (ACT_FET_S zone to J124.1, B.Cu); `inner_power_pyro` 2.65 mm (BAT_IN In2 to R134.1); `gate_servo` none under 0.5 mm on 8 layer pairs; `inner_signal` In2_rigid_exempt 3.4 mm (D70); rigid `ch1_parts` / `ch1_copper` / `pyro_block_area` digests equal R7's (the check passes them) |
| `tools/test_r8_check.py` | 23 tests OK; drain-case mutant fails as intended (§0) |
| Seeded DRC (scratch copy with `m3.kicad_pro` / `m3.kicad_dru`; deleted) | RAW_ACT B.Cu track beside J124.1: `rule 'Pyro E: RAW_ACT to bus and igniter (ARM break)' clearance 1.0000 mm; actual 0.7500 mm`. GND via 0.45 mm from the PYRO1_OUT track: `rule 'Pyro D: GND to bus, igniter and drain' clearance 0.5000 mm; actual 0.4500 mm`. BAT_ENABLE track 0.40 mm from J121.1: `rule 'Pyro F: … to other live nets' clearance 0.5000 mm; actual 0.4000 mm`. kicad-cli loads the custom rules |
| `m3.kicad_dru`, `check_actuators.py`, `m3.kicad_pro` | `git diff 431025d` empty; DRU SHA-256 `1674d58b…` = `check_actuators.DRU_SHA`; check_actuators `5de1eb3c…` = `check_r8.CHECK_ACTUATORS_SHA` |
| `pyro.kicad_sch`, `actuator_power.kicad_sch`, `battery_entry.kicad_sch` | differ from 431025d only in `(rev "M3-ASSY-R8")` |
| Zone fills | a native `ZONE_FILLER` refill in memory reproduces the saved fills (14 zone/layer sets, 0 differences), so the figures below are on current fills |

## 2. Arming break (AGENTS §2.1, §2.2; F8)

- **Netlist** (unchanged, `0cc1ed69…`; check_actuators rules 1–3 at pad level): PYRO1_BUS = {J124.1, R132.1, R134.2};
  PYRO1_IGN = {J121.2, R134.1}; PYRO1_OUT = {C128.1, J121.1, Q124.5, R131.1, R173.1}; J124.2 is RAW_ACT, Q121's drain,
  after the actuator switch. No test point on BUS / IGN / OUT. With the link out, every path into the igniter is a
  10 kΩ-class divider or pull-up (≤ 0.14 mA, pass-1 arithmetic, Inference).
- **Battery-live nets are complete in `BATTERY_LIVE`** (Measured from the netlist): the only low-impedance nets live with
  the switch open are BAT_IN (J1.1, D8, C80 / C88 / C89 / C95 / C96, Q120's drain) and ACT_FET_S (Q120's body diode). The
  others are behind ≥ 280 kΩ (BAT_SW_SOURCE / RETURN 470 kΩ, BAT_ENABLE 470 / 300 kΩ, BAT_OVLO 2 MΩ / 280 kΩ) or behind
  a capacitor (BAT_DAMP through C89 / C95; BAT_DVDT through C81).
- **Copper:** DRC 0. Rule E's closest is 1.300 mm (RAW_ACT F.Cu and B.Cu pours to J124.1). Battery-live copper on the same
  layer as BUS / IGN / OUT is ≥ 1.089 mm.
- **The barrels** (`barrels.py`; J124.1 (10.0, 95.86) BUS, J124.2 (10.0, 90.78) RAW, J121.1 (36.0, 90.78) OUT,
  J121.2 (36.0, 95.86) IGN, Ø2.6 / 1.6 mm): on In1 and In2 only GND at rule D's 0.501 mm and the other pin of the same
  terminal at 2.48 mm.
- **Holes:** pyro and RAW_ACT holes are ≥ 1.0 mm wall to wall from every foreign hole. The nearest are GATE_N via
  (23.0, 88.33) to GND via (22.85, 89.63), 1.009 mm, and J121.2 to GND via (34.25, 94.75), 1.122 mm. No CAF-class pair.
- **Inner rasters** under every CH1 pad (+0.5 mm, 0.1 mm grid; `under.py`): only GND, antipad voids, the pad's own net
  and block-internal pyro vias. RAW_ACT appears only under J124.2, its own pad.

## 3. Gate defined off (AGENTS §2.4; F6, F8)

Unchanged netlist and values, all pinned by check_actuators 4 / 4b / 4c / 16:
- R126 220 Ω series; R127 1 kΩ to GND at the MCU side; R128 10 kΩ and C126 220 nF gate to source;
  AON7524 pinned C431195.
- U1.3 = PE4 = PYRO1_GATE_N. Its neighbours U1.2 / U1.4 / U1.5 are no-net sentinels (rule 5).

AON7524 V_GS(th) is 0.4 V minimum and I_GSS ±10 µA (AOS AON7524 datasheet p. 2,
https://www.aosmd.com/res/datasheets/AON7524.pdf). In reset every GPIO is analog / high-Z (R8_DECISIONS l.93, DS12110
§3.8), so R127 holds the gate off. I_GSS × 1.09 kΩ is about 11 mV (Inference).

The bootloader path is now covered by constraint 11 (§0). The gate and GATE_N neighbour lists are identical to pass 2:
- GATE_N via (18.75, 54.3) 0.220 mm to the ARM1_SENSE lane, 0.450 mm to In2 3V3;
- GATE_N–CONT lane 0.300 mm (rule G);
- U1.3 0.700 mm to U1.1.

## 4. `m3.kicad_dru` pyro rules and the check_actuators contract

The DRU is R7's, unchanged and pinned. After rule H come only the small-pad thermal rule (no clearance), "RAW_ACT pins to
pours" (RAW_ACT THT pads to GND zones only) and J2's Tag-Connect rule, so nothing later lowers a pyro rule. Closest
approach per rule (Measured, `rules.py`, conditions transcribed from the DRU; same layer, pads / tracks / via rings /
fills):

| Rule | Min | Pass 3 closest | Where | Pass 2 |
|---|---:|---:|---|---:|
| A RAW_ACT to gate / sense / mid | 0.5 | 0.501 | RAW_ACT B.Cu box to the PYRO1_CONT lane; F.Cu pour to C127.1 (gate pad R127.1 1.115) | 0.501 |
| B bus / igniter / drain to gate | 0.5 | 0.670 | Q124.5 to the PYRO1_GATE track (block-internal) | 0.670 |
| C bus / igniter / drain to sense | 0.3 | 0.377 | PYRO1_BUS track to R132.2 | 0.377 |
| D GND to bus / igniter / drain | 0.5 | 0.501 | GND_B pour to J124.1, J121.1, J121.2 | 0.500–0.501 |
| E RAW_ACT to bus / igniter | 1.0 | 1.300 | RAW_ACT F.Cu / B.Cu pours to J124.1 | 1.300 |
| F bus / igniter / drain to other live | 0.5 | 0.700 | BAT_ENABLE track to R134.1 / R134.2 | 0.700 |
| G gate in the block to other live | 0.3 | 0.300 | GATE_N lane (x 18.75) to the PYRO1_CONT lane | 0.300 |
| A2 RAW_ACT to RAW_ACT_SENSE | 0.3 | none within 0.9 mm | | none |
| H live pads to sense / gate pads | 1.0 | 1.025 | Q124.5 to R129.2 | 1.025 |

check_actuators passes on the board (rule texts, minima, nets, per-rule hashes, PYRO_BLOCK, pinned parts, ACT_NETS).
PYRO_BLOCK still covers x 4–42, y 84–114.4 on all four copper layers. It holds 40 GND vias (centres inclusive of the
boundary; R7 22), as M3_R8 l.359 states.

## 5. D18, D19 (independent)

- **D18** (`d18.py`; In1 / In2 copper of every non-GND net in plan view against BUS / IGN / OUT copper on any layer,
  J124's pads exempt):
  - BAT_IN In2 2.650 mm to R134.1 (D97's trim leaves it unchanged; the island now ends at x 33.5, y 112.6, ≥ 4.8 mm from
    J121);
  - ACT_GATE via 2.790 mm, BAT_ENABLE via (40.42, 93.5) 3.178 mm, RAW_ACT In2 west 3.260 mm.
  - Pyro-family items aside: the D70 ARM1_SENSE In2 link (under the BUS track, In1 GND between), the PYRO1_CONT exit
    via 0.715 mm and the TP122 via 1.250 mm.
  - Met, identical to pass 2.
- **D19:** PYRO1_GATE_N's nearest servo copper is 5.890 mm on every layer pair (B.Cu lane to J122.1). Met.

## 6. What fix pass 2 changed near armed and pyro-control copper, and its fail-safe direction

`diffboards.py` (`6600ef94…` → `990c8040…`) changed these items:
- tracks: BAT_ENABLE's spine split at y 92.1 plus R81.1's 0.82 mm stub; one GND link by C83 (x ≈ 10, y 35);
- vias: four 0.6 → 0.5 mm (camera / RAW_PROTECTED area, y 32–61); step-7 GND (39.0, 91.3) → (38.85, 91.3) and
  (43.0, 91.5) → (42.9, 91.45); new GND (44.65, 86.775) (U9.8) and (13.5455, 74.2255) (J123.2's island);
- footprint: R81 (41.245, 91.0, 0°) → (39.6, 91.275, 90°), bottom;
- zone: R8_BAT_IN_In2 trimmed to x 12.4–33.5, y 100.3–112.6.

No PYRO1_* or ARM1_* copper changed. Re-running pass 2's neighbour sets on both boards gives identical `gate`, `sense` and
`bare_gate` lists. The `armed`, `bare_armed` and drain (`outn`) lists differ only at R81 and one via:

| Item | Before (`6600ef94…`) | After (`990c8040…`) | One bridge or leak does (Inference) | Direction |
|---|---|---|---|---|
| R81.1 BAT_ENABLE (bare, B.Cu) to J121.1 (drain, bare) | 2.720 mm | 1.825 mm | link out: OUT (≈ 1.5 V through the cold pull-up) holds EN above its threshold, so the board latches on; link in, armed: EN at bus voltage, U9 cannot be switched off. R165 470 kΩ / R81 300 kΩ pass µA only, so no fire | latch class; recorded (R8_VALIDATION l.486, D100) |
| R81.2 GND (bare, B.Cu) to J121.1 | none; nearest foreign bare GND pad was R83.2, 2.205 mm | 1.825 mm, the drain's nearest foreign bare GND pad | armed and powered: drain to GND bypasses Q124, so it **fires** (the GND row's direction) | bare to bare, L10 met (courtyard to pad 1.58 mm ≥ 1.5 mm; `l10.py`); R7 had U7.8 at 1.630 and R70.2 at 1.825 mm from the same J121.1 (rigid position) → R8P3-PYRO-02 (records) |
| GND via (38.85, 91.3), tented | 1.450 mm (at (39.0, 91.3)) | 1.300 mm to J121.1 | as above, needs a mask breach | rule D 0.5 mm; fine |

The other fix-pass-2 copper is ≥ 9 mm from armed copper:
- U9.8's via is 9.5 mm from J121.1;
- J123.2's island via sits 4.6 mm west of the ARM1_SENSE lane and outside every pyro neighbour list within reach;
- the four 0.5 mm vias lie at y ≤ 61, on non-pyro nets.

The In2 BAT_IN trim moves battery copper away from the block's east side. The R81 move also takes the BAT_IN feed from
between R81's pads (D100). The feed stays 3.7 mm from J121's pads on B.Cu.

## 7. Coating and leakage

- Bare pyro-gate copper to bare bus / igniter copper is unchanged: 1.027 mm (R126.2–R134.2) and 1.491 mm (C126.1–R134.1),
  the rigid block, as R7. No bare 3V3 / RAW_ACT / always-live pad lies within 5 mm of a pyro gate pad except the block's
  own copper (`bare_gate` identical to pass 2).
- TP122 (bottom, bare PYRO1_GATE, coated last): GND 1.001, ARM1_SENSE via 1.260, RAW_ACT pour 3.200, GATE_N 3.220 mm.
- TP121 (ACT_GATE, top, uncoated per ORDERING): GND and RAW_ACT pours 1.001 mm, R121.2 1.330 mm. Unchanged.
- ORDERING §5's coating list, static / leakage / dynamic gates, plug-out cold test and the H-6(b) "RAW_ACT dead with the
  switch open" step are unchanged and still cover the block. R81 is not a coated part, and nothing requires it to be
  (its pads fail to the latch class or GND, see §6).

## 8. A8 (TP122's in-pad PYRO1_GATE via)

Re-measured:
- TP122 at (20.45, 92.4), bottom, Ø1.5 mm; via 0.6 / 0.3 mm at its centre, hole edge 0.60 mm inside the pad edge;
- nearest GND vias 2.717 mm (22.875, 93.625), 3.665 and 3.761 mm; nearest foreign copper 1.001 mm (GND_B);
- route_check: 0 out-of-date no-GND reasons.

Unchanged; the allowlist reason holds.

## 9. Findings

### R8P3-PYRO-01 (Minor, not worth fixing; dispositions fix pass 2's "candidate for pass 3"): the R120.2 GND via is not the actuator gate's closest GND copper, so moving it gains nothing

- **Requirement:** AGENTS §2.2 / F8 H-6(b): the power switch keeps RAW_ACT, and so the bus, dead while open. check_actuators
  l.140–141 names the hazard: "a GND short on ACT_GATE or ACT_DRV left Q120/Q121 on with the power switch open".
  AGENTS §2.5 requires records to state what was measured.
- **Finding:** fix pass 2's handoff ("Not done") and R8_VALIDATION (ACT_GATE observation row l.492, C12b #19 l.379,
  "Open after fix pass 2" l.518–519) present step 7's GND via (15.0, 107.3), 0.180 mm from bare R120.2, as the specific
  gap. They propose giving `make_ground.clearance` the actuator gate nets in pass 3. On the board, the GND pours already
  sit at the 0.151 mm netclass edge from every bare ACT_GATE / ACT_DRV pad, R120.2 included. Moving or dropping the via
  would leave the ACT_GATE–GND minimum at 0.151 mm on the same pad. This is R7's accepted class: R7 had four such pads at
  0.151 mm. The bridge direction is the switch turning on with the power switch open: RAW_ACT live, and the bus live with
  the link in. Q124 stays held off by R127 / R128 with the logic unpowered, so it does not fire by itself (Inference).
  The bench screens it. ORDERING l.168 has an unconditional hot check: RAW_ACT below 0.1 V with the switch open at
  ≥ 70 °C. ORDERING l.159 has the H-6(b) "RAW_ACT dead with the switch open" step.
- **Evidence (Measured, `actgnd.py`):** on `990c8040…`:

  | Pad | Net | Layer | GND copper |
  |---|---|---|---|
  | R120.2 (14.3, 107.16) | ACT_GATE | B.Cu | GND_B pour 0.151 mm; via (15.0, 107.3) 0.180 mm |
  | C120.2 (12.5, 107.16) | ACT_GATE | B.Cu | GND_B pour 0.151 mm |
  | R121.1 (13.48, 100.85) | ACT_GATE | F.Cu | GND_F pour 0.151 mm |
  | R121.2 | ACT_DRV | F.Cu | GND_F pour 0.151 mm |
  | Q122.3 | ACT_DRV | F.Cu | GND_F pour 0.151 mm |

  On R7 `c872a3d3…`, Q121.4, R121.1, R121.2 and Q122.3 each sit 0.151 mm from the GND_B pour; Q122.3 also has a GND
  via 0.425 mm away. All the pour edges are under mask, and the pads have 0 mask margin (board `pad_to_mask_clearance 0`;
  vias tented both faces).
- **Fix:** no board change. Close the candidate in the records:
  - Change R8_VALIDATION's ACT_GATE row, C12b #19, "Open after fix pass 2" and `fix2_handoff.md`'s "Not done" to
    "GND pours stand at 0.151 mm from all five bare ACT_GATE / ACT_DRV pads, as R7 (four pads); step 7's via at 0.180 mm
    adds no closer approach; screened by ORDERING's hot RAW_ACT check".
  - Raising it would need a new GND-to-ACT_GATE / ACT_DRV clearance on the pours. That is a DRU change against the
    pinned `m3.kicad_dru` (check_actuators DRU_SHA) for a non-firing, bench-screened fault, and it is not proposed.

### R8P3-PYRO-02 (Minor, worth fixing, records): D100 put a bare GND pad 1.825 mm from the drain barrel, and the pyro observations' GND row omits it

- **Requirement:** AGENTS §2.5. The observations table claims to give "every new net near the armed copper … with its
  fail-safe direction"; fix pass 2 corrected its GND row (R8P2-PYRO-02) because GND on the drain fires.
- **Finding:** D100 stood R81 vertical at (39.6, 91.275), bottom. Its GND pad R81.2 (39.6, 90.45) is now 1.825 mm,
  bare to bare on B.Cu, from J121.1 (PYRO1_OUT, the drain's terminal barrel, bare bottom ring). It is the drain's nearest
  foreign bare GND pad; on `6600ef94…` that was R83.2 at 2.205 mm. A bridge fires an armed, powered channel. That is the
  direction R8P2-PYRO-02 put on record (Inference).

  The geometry is acceptable:
  - R81's courtyard is 1.58 mm from J121.1's pad, so R5 L10 (≥ 1.5 mm) is met.
  - R7 had U7.8 at 1.630 mm and R70.2 at 1.825 mm from the same J121.1 (rigid position (36.0, 90.78)).
  - The plug-out cold test (FMEA H-1) and the static gate detect a drain-to-GND path before any real igniter.

  D100 records the distance ("1.825 mm from J121.1 (bare to bare; rule D's 0.5 mm)"). The safety table does not.
  - Its GND row lists only pours and the two tented vias.
  - Its closing sentence names R81.1 (BAT_ENABLE) for the 1.825 mm bare-to-bare pair but not R81.2 (GND).
  - M3_R8 l.359–368 gives the same pours-and-vias picture.
- **Evidence (Measured):** `baregnd.py`, foreign bare GND pads to bare armed pads, same layer:

  | Board | Nearest to the drain J121.1 |
  |---|---|
  | `990c8040…` | 1.825 mm, J121.1–R81.2 (B.Cu) |
  | `6600ef94…` | 2.205 mm, J121.1–R83.2 |
  | R7 | 1.630 mm, J121.1–U7.8; 1.825 mm, J121.1–R70.2 |

  `pos.py`: R81.2 at (39.6, 90.45), bottom. `l10.py`: R81 courtyard to J121.1 is 1.58 mm.
- **Fix:** add to the GND row of R8_VALIDATION's pyro observations, and to M3_R8 l.364, for example: "R81.2 (bare GND
  pad, since D100) 1.825 mm from J121.1's bare bottom ring, the drain's nearest bare GND pad (R7: U7.8 1.630 mm); L10
  met". Also extend the closing sentence to "R81.1 / R81.2–J121.1 1.825 mm".

## 10. Observations (no finding)

- **Records checked against the board, all exact:**
  - M3_R8's "7 nets within 3 mm of armed copper": BAT_ENABLE 0.700, ACT_FET_S 1.089, RAW_ACT 1.300, BAT_OVLO 1.922,
    RAW_PROTECTED 1.975, BAT_DAMP 2.450, ACT_GATE via 2.521 mm.
  - "40 GND vias in PYRO_BLOCK, nearest armed-live 0.522 mm (J121.2)".
  - D18 2.65 mm; the drain's battery copper 3.562 mm.
- **Plan-view neighbours across the whole core:** the B.Cu BAT_IN pour lies 0.950 mm in plan from R134's F.Cu pads. The
  two are separated by the full 1.6 mm stack with In1 / In2 GND between, so it is not a bridge or prepreg-adjacency pair.
  D18 covers the prepreg-adjacent inner layers.
- **Rule G (0.300 mm, GATE_N–CONT lane) and the GATE_N via 0.220 mm from ARM1_SENSE** remain pass 1's R8P1-PYRO-04 class:
  a hard short leaves the gate near 0.37 V in reset against the 0.4 V minimum threshold. ORDERING l.154 repeats the static
  gate warm. No new information changes that disposition.
- **Constraint 11's two options:** if the firmware takes the GPIOE-reset option first, PE9 also goes analog before the
  SX1262 can be put to sleep, so the radio is simply held in reset by R311. That is harmless and still meets F10
  (Inference).
- **Scratch:** the scratch board copies (`seed/`, the `tools` mutant copy) are deleted. The extracted comparison boards
  (`pre/`, `r7.kicad_pcb`) are deleted after this report. Only small scripts and text outputs remain in
  `p3pyro/`.
