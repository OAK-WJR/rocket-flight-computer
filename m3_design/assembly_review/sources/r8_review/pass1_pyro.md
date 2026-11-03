# R8 review pass 1: pyro and arming safety

Reviewer: independent, read-only (no repository file changed but this report; the board and schematic were never
saved). Board `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`429b6db4dc95c1a0fd3e736625c416c20fa0e7fc72f6f6c9c576003340dc1987` (confirmed before and after the review);
baseline R7 `c872a3d3…` (extracted read-only with `git show 431025d:m3_design/assembly_review/m3.kicad_pcb` into the
session scratchpad for comparison; `../rocket-flight-computer-r7` was not touched).

**Verdict: 0 Critical, 0 Major, 4 Minor** (three cheap ones marked worth fixing). The arming break is complete in the
netlist and in copper, the gate is defined off in reset and unpowered, every `m3.kicad_dru` pyro rule is loaded and met,
`check_actuators` holds, and D18 / D19 hold with margin. Around the armed copper R8 is much cleaner than R7: 7 foreign
nets within 3 mm of armed copper against R7's 23, and no servo, camera or 3V3 copper near the block. What the
re-placement made worse is local and DRC-legal. Two pours now sit at the pyro rules' minimum beside safety-critical
copper (R8P1-PYRO-01, -02): ACT_FET_S, which is battery-live whatever the power switch does, at 0.501 mm from J124.1,
and RAW_ACT at 0.696 mm from a bare PYRO1_GATE_N pad (R7: 1.042 mm). A prototype on a scratch copy shows that both
can be widened to at least 1.0 mm by editing outline vertices in `r8_power.py`. Both 7.7 A necks stay the same
(ACT_FET_S 4.97 mm, RAW_ACT 5.90 mm at the 0.1 mm grid), and DRC, `route_check` and `check_r8` stay clean. The records miss these adjacencies, and they miss BAT_ENABLE's run through the block
(R8P1-PYRO-03).

Labels: **Measured** = pcbnew on the board above (scripts in the session scratchpad, `pyro/measure.py`, `under.py`,
`zones.py`); **Datasheet** = cited maker document; **Inference** = reasoning not measured (AGENTS §2.5).

## 0. Previous findings in this dimension

This is the first R8 review pass, so there is no earlier R8 pyro finding to close. Pyro-relevant R7 items that R8 had
to carry:
- R7 E2 (PE4's SPI4 / TRACE alternate functions): carried. `step9/r8_binding_note.json` says "Lock PE4 (GPIOE_LCKR)
  before any other GPIOE set-up; SPI4 is never enabled". R8 puts more functions on GPIOE (UART7 PE7/PE8, RADIO_NRST
  PE9, DIO1 PE15), so the lock matters more; it stays a firmware-binding item.
- R7 P5-ROUTING_GEOMETRY-03 (GND return vias at ARM1_SENSE's In2 link): carried. `route_check` r8 reports 0 failing
  critical-via-no-GND items; A8 is the only allowlisted one.
- R7 P6-DOCS-04(d) (J124 fuse legends far from J124): carried. "J124: 5A FAST / 2S" at (19.36, 87.04) and "J124
  2-FUSE-1: ARM LAST" at (21.97, 95.98), both within `legend_subjects`' 6 mm.
- R7's accepted adjacency list (C15) is superseded. PYRO1_CONT's close R7 neighbours (CAM_UART_OE, SWCLK, NRST and
  3V3A at 0.175–0.212 mm) are gone, and R7's GATE_N neighbours (SERVO2_MCU 0.208 mm, QSPI_IO2 0.258 mm, In2 servo
  lanes 0.30 mm) are gone. Among non-pyro signals, the pyro control nets' nearest R8 neighbour is NRST, 0.300 mm from
  the ARM1_SENSE lane (B.Cu (18.83–27.5, 52.45)). A short would hold the MCU in reset: the board is dead at bring-up
  and the gates stay off. The rest are in sections 6 and 10.

## 1. Gate runs (this pass)

| Run | Result |
|---|---|
| `tools/check.sh` (unchanged board) | exit 0: DRC 0 violations at every severity, 0 unconnected, 0 parity, ERC 0; audit OK; silk OK; `R8 CAD contract: OK`; route_check r8 0 failing / 3 allowlisted / 0 stale; `actuator safety contract: OK`; fit OK. `git status` was identical before and after |
| `check_r8` evidence | `inner_power_pyro` nearest 2.65 mm (BAT_IN In2 zone to R134.1); `gate_servo` none within 2.0 mm on the close layer pairs; `inner_signal` In2_rigid_exempt 3.4 mm (D70) |
| `tools/test_r8_check.py` | 20 tests OK, including the D18 and D19 seeded-defect tests |
| Seeded DRC (scratch copy) | a RAW_ACT track 0.75 mm from J124.1 gives `Clearance violation (rule 'Pyro E: RAW_ACT to bus and igniter (ARM break)' clearance 1.0000 mm; actual 0.7500 mm)`: kicad-cli loads the custom rules |
| `m3.kicad_dru`, `check_actuators.py` | unchanged from 431025d (git diff empty); check_actuators SHA-256 `5de1eb3c…` = `check_r8.CHECK_ACTUATORS_SHA`; its DRU_SHA and per-rule hashes pass |

## 2. Arming break (AGENTS §2.1, §2.2; F8)

- **Netlist (Measured, `schematic.net.xml` and board pads):** PYRO1_BUS = {J124.1, R132.1, R134.2}; PYRO1_IGN =
  {J121.2, R134.1}; J124.2 is RAW_ACT; RAW_ACT is Q121's drain, behind the logic-gated switch; no test point on BUS,
  IGN or OUT; no pyro terminal pin on BAT_IN (check_actuators 1, 2, 3). `pyro.kicad_sch`, `actuator_power.kicad_sch` and
  `battery_entry.kicad_sch` differ from 431025d only in their revision string (`git diff`).
- **With the link out, every path into the igniter is high impedance (Inference from the netlist values):** 3V3 →
  D120 → R131 10 kΩ → OUT → igniter → R134 → BUS → R132 + R175 10.2 kΩ → 1 kΩ gives ≤ 0.14 mA. An MCU sense pin
  wrongly driven high (PC5 via R170 4.7 kΩ, PC0 via R168) gives ≤ 0.2 mA through the igniter. All are far below the
  ≥ 20 mA no-fire assumption. Nothing bypasses J124.
- **Copper:** DRC 0 (no short, no unconnected item). Rule E closest is 1.30 mm (RAW_ACT F.Cu and B.Cu pours to J124.1;
  R7 1.001). On the inner layers, nearest RAW_ACT / BAT_IN to BUS / IGN / OUT is 2.65 mm (D18 ≥ 2.5), J124.2's own
  ring (2.48 mm, exempt) aside.
- **Other battery-derived copper near BUS / IGN** (same layer; Measured): ACT_FET_S 0.501 mm (B.Cu pour to J124.1's
  ring; R8P1-PYRO-01), RAW_PROTECTED 1.975 mm (F.Cu track y 99.75 to R134), BAT_IN 3.015 mm (via (21.25, 100.9) to
  R134.2). R7 had BAT_IN at 0.501 mm on B.Cu and In2, 3V3 at 0.55 mm (F.Cu via at R134.2) and CAM_5V at 1.30 mm
  (In2, J121.2).
- **In1 / In2 under the CH1 pads, +0.5 mm** (0.1 mm raster, `under.py`): only GND, antipad voids and each pad's own
  net. RAW_ACT appears only under J124.2, its own pad. The plan's "In2 GND under the CH1 pads" holds.

## 3. Gate defined off (AGENTS §2.4; F6, F8)

- Series R126 220 Ω, R127 1 kΩ on the MCU side, R128 10 kΩ and C126 220 nF gate to source (check_actuators 4, 4c;
  values pinned by LCSC code). The total DC gate-to-source resistance is 10 kΩ ∥ 1.22 kΩ = 1.09 kΩ, inside MARGIN's
  ≤ 10 kΩ.
- AON7524: V_GS(th) 0.4 / 0.8 / 1.2 V min / typ / max at 250 µA; I_GSS ±10 µA at ±10 V; Q_gd 5.2 nC typ (Datasheet:
  AOS AON7524 Rev 1.1, Oct 2023, p. 2, https://www.aosmd.com/res/datasheets/AON7524.pdf). I_GSS × 1.09 kΩ = 11 mV.
  The Miller step at link insertion is about Q_gd / C126 = 24 mV. Both are far below 0.4 V (Inference from the
  datasheet values).
- PE4 is analog / Hi-Z in reset and is not driven by the ROM bootloader (`pin_table.tsv` row 3: DS12110 §3.8,
  Table 8; AN2606 Table 135). Its neighbours pins 2 and 4 are still no-net sentinels (check_actuators 5). R127 sits at
  the block end of the 40 mm GATE_N lane, so the lane is held low at the FET end.
- The leakage hold is unchanged from R7. Leakage of 13–22 kΩ from 8.4 V turns the FET on: 8.4 × 1.09 / (21.7 + 1.09)
  = 0.40 V at V_GS(th) min, so the ORDERING figure is consistent with the datasheet.

## 4. `m3.kicad_dru` pyro rules and the check_actuators contract

The DRU is R7's, unchanged and pinned. KiCad applies the last matching rule. After rule H come only the thermal-relief
rule (no clearance), "RAW_ACT pins to pours" (RAW_ACT through-hole pads to GND zones, no pyro pair) and the J2
Tag-Connect rule (it can only raise clearance near J2, which is far from any pyro copper). None lowers a pyro rule.
Closest approach per rule (Measured; it agrees with M3_R8):

| Rule | Min | R8 closest | Where | R7 |
|---|---:|---:|---|---:|
| A RAW_ACT to gate / sense / mid | 0.5 | 0.501 | RAW_ACT F.Cu pour to C127.1 (CONT); the gate pair is 0.696 to R127.1 | 0.95 (CONT) / 1.042 (GATE_N) |
| B bus / igniter / drain to gate | 0.5 | 0.52 pad to pad (Q124.4 to Q124.5, the FET's own pads, exempt); 0.67 otherwise | block-internal | same |
| C bus / igniter / drain to sense | 0.3 | 0.377 (M3_R8's figure; the nearest non-exempt pair this pass found was 0.410, the bus track to the ARM1_SENSE via (14.55, 94.15); DRC 0 proves ≥ 0.3) | block-internal, rigid | same |
| D GND to bus / igniter / drain | 0.5 | 0.501 | pours | 0.501 |
| E RAW_ACT to bus / igniter | 1.0 | 1.300 | pours to J124.1 | 1.001 |
| F bus / igniter / drain to other live | 0.5 | 0.501 | ACT_FET_S B.Cu pour to J124.1 | 0.501 (BAT_IN B.Cu, In2) |
| G gate in the block to other live | 0.3 | met (DRC 0) | GATE_N lane x 18.75 inside y ≥ 84 keeps ≥ 0.3 | — |
| A2 RAW_ACT to RAW_ACT_SENSE | 0.3 | none near in the block; 0.294 is R177's own pads (one part) | | 0.358 |
| H live pads to sense / gate pads | 1.0 | 1.025 | Q124.5 to R129.2 | 1.025 |

## 5. D18, D19, D20

- **D18** (independent, In1 / In2 power copper in plan view against every layer's BUS / IGN / OUT, J124 exempt):
  2.65 mm (BAT_IN In2 zone to R134.1), then RAW_ACT In2 west 2.70 mm and the RAW_ACT via (5.5, 97.0) 2.90 mm, both
  to J124.1. Met.
- **D19** (independent, every layer pair, not only the close ones): GATE_N's nearest servo PWM copper is 5.89 mm
  (B.Cu lane to J122.1). Met with a wide margin (R7: 0.000 mm).
- **D20:** only R7's 3.4 mm ARM1_SENSE In2 link (D70). It runs under the 1 mm F.Cu PYRO1_BUS track (y 94.86–95.86),
  and In1 is solid GND between them (sampled at x 14.55, y 94.9–95.8).

## 6. Every new net near armed and pyro-control copper, and its fail-safe direction

Within 3 mm of armed copper (PYRO1_BUS / IGN / OUT, any layer; Measured; the same 7 nets as M3_R8), plus new copper
near the block's sense, gate and actuator-gate pads, which the records did not survey. The effect of one bridge or
short is given for each (Inference from the netlist; R = resistor values from the schematic):

| New neighbour | Closest (mask state) | Effect of one bridge / short | Direction |
|---|---|---|---|
| ACT_FET_S pour | 0.501 mm to J124.1 ring, B.Cu (masked pour, bare ring); 0.301 mm to ARM1_SENSE via (14.55, 97.55) | Battery (through Q120's body diode, switch open or not) onto BUS, so the ARM link is bypassed; no fire unless Q124 also turns on; ARM1_SENSE reads "armed" with the link out. On the sense via, 8.4 V reaches PC5 (TT_a) through 4.7 kΩ | unsafe (latent loss of the barrier) / pin stress |
| RAW_ACT F.Cu pour | 0.696 mm to bare R127.1 (GATE_N); 0.501 mm to bare C127.1 (CONT) | GATE_N: the gate goes to about 8.2 V through R126 / R128 and an armed channel **fires**. CONT: 8.4 V into PC0 through R168 4.7 kΩ, about 1 mA, no fire | GATE_N unsafe; CONT benign |
| BAT_ENABLE track (U9 EN, 227 kΩ) | 0.70 mm to both R134 pads; 0.216 mm to bare R175.2 (ARM1_SENSE); 0.40 mm to Q122.1 (ACT_EN) and Q122.3 (ACT_DRV); 2.72 mm R81.1 to J121.1 (bare to bare, B.Cu) | To BUS / IGN when armed, or to ACT_EN: EN held high, so the switch cannot turn the board off. To ACT_DRV with the switch open: EN about 5.6 V and V_GS about −1.9 V, so the board and RAW_ACT cycle on (Inference). To ARM1_SENSE: EN pulled to ≤ 0.75 V, so the board will not start. To OUT: latched on through the cold pull-up, and EN collapses when Q124 fires | defeats the power switch (FMEA H-6(b)); never fires by itself |
| BAT_OVLO (R82.2) | 1.92 mm to J121.1, bare to bare, B.Cu | OUT high, so U9's OVLO trips and the board browns out (relaxation) | no fire; loss of primary |
| RAW_PROTECTED track | 1.975 mm to R134 | U9-limited supply onto BUS when on, so the link is bypassed; no fire alone | latent |
| BAT_DAMP (C89.2) | 2.45 mm to R134.1, bare to bare | IGN to GND through R166 0.33 Ω: armed, about 3.6 A in R134, which overheats; misfire | no fire; loss of primary |
| ACT_GATE via | 2.52 mm to J124.1 | Armed: the switch fights itself (oscillates); link out: BUS fed through R120 100 kΩ, ≤ 77 µA | no fire |

All seven are farther than R7's equivalents or new in kind. Every bare-to-bare figure is ≥ 1.92 mm. The four closest
items (ACT_FET_S, RAW_ACT at R127.1, BAT_ENABLE at R175.2 and at Q122) are masked copper next to a bare pad, so a
bridge needs a mask breach. Whether they need work is decided in the findings below.

## 7. Coating and leakage

- Bare pyro-gate copper to bare bus / igniter copper is 1.027–2.001 mm (rigid block, = R7). No bare 3V3, RAW_ACT or
  other always-live pad is within 5 mm of a pyro gate pad (Measured; confirms M3_R8). The masked RAW_ACT pour at
  0.696 mm from R127.1 is not "bare", so that metric does not see it (R8P1-PYRO-02).
- TP122 (bottom, bare PYRO1_GATE, coated last): neighbours GND 1.001, ARM1_SENSE via 1.26, RAW_ACT B.Cu pour 3.20,
  GATE_N 3.22, BAT_IN 5.45 mm.
- TP121 (ACT_GATE, top since R8, kept uncoated by ORDERING §5): GND and RAW_ACT pours 1.001 mm (its 1.0 mm local
  clearance; both masked), ACT_DRV R121.2 1.33 mm. ACT_GATE is a 100 kΩ node: a leak of a few hundred kΩ to GND turns
  the actuator switch on with the power switch open (Inference; that rule H covers ACT_GATE is consistent with this).
  ORDERING's "RAW_ACT dead with the switch open" bench step covers it.
- TP80 (bare BAT_IN test pad, bottom (43.4, 94.6), probed in the pack-change rule) now lies inside the PYRO_BLOCK area,
  5.37 / 5.64 mm from J121.2 / J121.1's bare joints. A probe slip feeds the igniter only through the 10.2 kΩ dividers,
  ≤ 0.75 mA (Inference): no hazard; listed for completeness.

## 8. A8 (TP122's in-pad PYRO1_GATE via)

Re-measured: TP122 at (20.45, 92.4), bottom, Ø1.5 mm pad; via 0.6 / 0.3 mm at its centre (locked); hole edge 0.60 mm
inside the pad edge; nearest GND vias 2.717 mm (22.875, 93.625), 3.665 mm, 3.761 mm; nearest foreign copper 1.001 mm
(GND_B, the pad's 1.0 mm local clearance). `route_check` re-ran `nognd_audit` (0 out-of-date reasons). The allowlist
reason holds; no current flows through the via.

## 9. Findings

### R8P1-PYRO-01 (Minor, worth fixing): battery-live ACT_FET_S pour at rule F's minimum from the ARM bus terminal

- **Requirement:** AGENTS §2.1 (the ARM plug is a complete break). F8 / rule E keep RAW_ACT 1.0 mm from BUS / IGN.
  D18 (plan_cleansheet §6.2) treats battery copper beside BUS / IGN as "the same ARM-bypass class" and keeps it 2.5 mm
  away on the inner layers.
- **Finding:** zone `R8_ACT_FET_S_B` (B.Cu, outline vertex (11.4, 97.6), `r8_power.py` BAND_ZONES) fills to 0.501 mm
  from J124.1's bare bottom ring (PYRO1_BUS, square 2.6 mm pad at (10.0, 95.86)), and to 0.301 mm from the ARM1_SENSE
  via (14.55, 97.55). ACT_FET_S is the common source of the back-to-back P-FETs. It sits a diode drop below BAT_IN
  through Q120's body diode whenever a pack is connected, switch open or not (`docs/CIRCUIT_REVIEW.md` line 370, for
  the same back-to-back topology, Q1 = today's Q120: "FET_S rises through Q1's body diode to BAT+ − Vsd ≈ 7.7 V"). So it is unswitched battery: stronger than RAW_ACT,
  which rule E keeps 1.0 mm away. It is under rule F's 0.5 mm only because the DRU names RAW_ACT in E. R7's ACT_FET_S
  was 1.200 mm from J124.1 (R7 had BAT_IN at 0.501 there instead). R8 removed BAT_IN from that spot and from In2, but
  brought ACT_FET_S in to the same minimum on the face where J124's through-hole joints are soldered.
- **Evidence:** Measured, `measure.py bypass` / `armed`: `0.501 PYRO1_BUS ACT_FET_S B.Cu J124.1 | zone
  R8_ACT_FET_S_B`; `0.301 ARM1_SENSE ACT_FET_S B.Cu via(14.550,97.550)`. R7 (`c872a3d3`): `1.200 PYRO1_BUS ACT_FET_S
  B.Cu`. R8_VALIDATION "Outside the list" records the 0.501 mm but not that the net is battery-live. Failure: a bridge
  (mask breach or debris at J124.1's bottom fillet) leaves BUS at battery voltage with the link out and the board off.
  The arming barrier is gone without anyone noticing until ARM1_SENSE is read with the link out. A fire then needs a
  second fault (Q124 on).
- **Fix (prototyped):** in `r8_power.py` BAND_ZONES `R8_ACT_FET_S_B`, replace vertex (11.4, 97.6) with (12.4, 97.6),
  a chamfer from (11.4, 98.6). On a scratch copy refilled natively: J124.1 gap 1.089 mm; the ACT_FET_S neck is
  unchanged (4.97 mm, 21.4 °C, cut box (11.8, 14.1, 98.0, 104.5); R 0.18 mΩ); DRC has no clearance or connectivity
  item. Optional: gate the margin in `check_r8` (BAT_IN / ACT_FET_S copper ≥ 1.0 mm from BUS / IGN on the outer
  layers, D18's sibling). The 0.301 mm to the sense via could also go to 0.5 mm (rule A's figure). That shortens the
  neck's north end slightly (Inference: about 0.2 mm, still within D12's 30 °C), so it is optional.

### R8P1-PYRO-02 (Minor, worth fixing): RAW_ACT pour moved in toward the CH1 gate and continuity pads

- **Requirement:** F8 / rule A (0.5 mm) and rule H's reason (1.0 mm between exposed RAW_ACT and gate pads, against a
  single bridge). D9 / D15: the block's R4 qualification is to carry over unchanged.
- **Finding:** zone `R8_RAW_ACT_F` (F.Cu, outline corners (21.3, 88.0) and (25.1, 86.3) / (21.3, 86.3)) fills to
  0.696 mm from bare R127.1 (PYRO1_GATE_N, the gate's MCU-side pull-down, (21.9, 88.83)), against R7's 1.042 mm. It
  fills to 0.501 mm from bare C127.1 (PYRO1_CONT) against R7's 0.950 mm. Rule A is met. Rule H does not apply because
  the pour is masked. A RAW_ACT-to-GATE_N bridge is the one single bridge that fires an armed channel directly: the
  gate goes to about 8.4 × 10 / 10.22 = 8.2 V through R126 (Inference). R8_VALIDATION's pyro observation names only
  C127.1, the benign one.
- **Evidence:** Measured, `measure.py pairs`: R8 `0.696 PYRO1_GATE_N RAW_ACT F.Cu R127.1 | zone R8_RAW_ACT_F` (0.696–0.697 mm over two runs, 0.5 µm bisection) and
  `0.501 RAW_ACT PYRO1_CONT F.Cu | C127.1 BARE`; R7 `1.042 … R127.1 BARE`, `0.950 … C127.1 BARE`. Both pads are inside
  the coated block, so a bridge needs a mask breach under the coating. The probability is low, but the consequence is
  the worst on the board.
- **Fix (prototyped):** (a) the gate pair, at no neck cost: in `R8_RAW_ACT_F`'s outline (`r8_power.py` BAND_ZONES),
  replace vertex `(21.3, 88.0)` with the chamfer `(21.3, 87.3), (20.6, 88.0)`. That gives R127.1 1.115 mm on the
  scratch copy. Measured with (a) and the R8P1-PYRO-01 trim together, at the 0.1 mm grid: RAW_ACT neck 5.90 mm, 17.6 °C,
  R 1.45 mΩ, the same cut (20.2–21.8, 80.75–86.25) as the board as built. (b) Optionally, the benign
  CONT pair: replace `(25.1, 86.3), (21.3, 86.3)` with `(25.1, 85.75), (23.2, 85.75), (23.2, 86.3), (21.3, 86.3)`.
  That gives C127.1 1.000 mm (use 85.7 for margin), but the neck moves to the new corner: 5.94 → 5.72 mm at the
  0.05 mm grid (17.5 → 18.3 °C; 5.90 → 5.74 mm at 0.1 mm; D12 needs ≥ 5.3 mm and ≤ 20 °C; R unchanged at 1.45 mΩ).
  Since a RAW_ACT-to-CONT bridge does not fire, (b) is a judgement call; (a) is the one that matters. With both applied, DRC has
  no clearance or connectivity item, `check_r8` passes (apart from a scratch-folder artefact) and `route_check` is
  unchanged (prototype check below).

### R8P1-PYRO-03 (Minor, worth fixing, records only): BAT_ENABLE runs through the block, and the records miss the new adjacencies

- **Requirement:** AGENTS §2.5 and §3 (records state what was verified), and r8_plan §3 step 9 ("pyro exits, coating,
  leakage").
- **Finding:** M3_R8 says "No signal net now passes the block". BAT_ENABLE, U9's enable node (R165 470 kΩ / R81 300 kΩ,
  C87; 227 kΩ Thevenin), runs on F.Cu from a via at (16.6, 104.5) north along x 16.6 to y 99.25, between Q122's pads (0.40 mm to Q122.1 ACT_EN and
  Q122.3 ACT_DRV). It passes 0.216 mm from bare R175.2 (ARM1_SENSE), then runs east along y 98.45 from x 17.4 to 42.9:
  25.5 mm, 24.6 mm of it inside PYRO_BLOCK (x ≤ 42), 0.70 mm from both R134 pads. The step-9 survey covered only nets near BUS / IGN / OUT.
  It does not list new copper beside the block's sense, gate and actuator-gate pads: RAW_ACT 0.696 mm to R127.1,
  ACT_FET_S 0.301 mm to the ARM1_SENSE via, BAT_ENABLE 0.216 mm to R175.2 and 0.40 mm to Q122. The fail-safe
  direction of each is in section 6. None fires by itself. Several defeat the power switch, which matters under FMEA
  H-6(b), where the switch is the pad arming device (FMEA V-18: "the reed switch becomes the only pad interlock",
  with no state readback). R7 had BAT_IN, a stiffer source, 0.35–0.40 mm from the same Q122 pads, and BAT_SW_RETURN
  1.125 mm from J121.2 (the same latch class), so this is not a regression in kind.
- **Fix:** correct M3_R8's sentence. Add the section-6 table (or its four masked-copper rows) to R8_VALIDATION's
  "Pyro review observations". Keep two ORDERING §5 steps: "RAW_ACT dead with the switch open", which catches the
  Q122 case, and the 20 power-switch cycles with the link in, RAW_ACT below 1 V between cycles, which catch the BUS
  latch. No copper change is proposed for BAT_ENABLE: rerouting it is a signal-family change and not cheap.

### R8P1-PYRO-04 (Minor, not worth fixing): GATE_N lane between the two sense lanes (hard-short margin)

- **Finding:** on B.Cu the three exits run as one bundle. PYRO1_GATE_N at x 18.75 runs parallel to ARM1_SENSE at
  x 18.18 for 33.5 mm, 0.37 mm edge to edge, and GATE_N's via (18.75, 54.3) is 0.22 mm from the ARM1_SENSE track.
  PYRO1_CONT is 0.30 mm away. Model a hard GATE_N-to-ARM1_SENSE short with the MCU in reset and the channel armed at
  8.4 V. ARM1_SENSE's Thevenin is 0.75 V behind 0.91 kΩ, and GATE_N's load is R127 ∥ (R126 + R128) = 0.91 kΩ, so the
  gate sits at about 0.37 V. AON7524 V_GS(th) min is 0.4 V at 25 °C (datasheet p. 2) and lower when hot (Inference).
  The margin is thin. With the MCU running, PE4 drives GATE_N low, so the gate is safe and ARM1_SENSE reads
  "disarmed". A CONT short self-limits, because CONT falls as Q124 conducts.
- **Why not worth fixing:** only a copper defect makes this short (both tracks and the via are masked or tented), and
  JLC's electrical test screens shorts (Inference). ORDERING's static gate (armed, MCU held in reset, ≤ continuity +
  0.1 mA) detects it. R7's GATE_N neighbours were toggling servo PWM and 3V3 at 0.21–0.32 mm, which was worse.
  Recorded for the bench plan: run the static gate also on a warm board, if convenient.

## 10. Observations (no finding)

- The MCU side of the sense paths sits 0.18–0.20 mm from the USB_LIMITED B.Cu lane (R172 pads; ARM1_SENSE_MCU via
  (29.3, 47.5)), on the MCU side of the 4.7 kΩ. M3_R8's exit table records this. A copper short puts 5 V on PB0 or PC5
  (PC5 is TT_a) only with USB connected. It is screened by the electrical test and is not a fire path.
- In2 under the exit lanes' B.Cu centrelines (0.2 mm samples): GATE_N 38.0 mm all GND (6 antipad voids); CONT
  45.4 mm all GND; ARM1_SENSE 52.1 mm GND except about 14.8 mm over the In2 3V3 region near R170 / U1, inside
  U1's field (D47's stated exception).
- 40 tented GND vias lie in the PYRO_BLOCK area; the nearest is 0.52 mm from J121.2 (rule D). A GND-to-IGN bridge
  loads the armed bus through R134 (up to about 4.1 A and 34 W, ORDERING §5) and does not fire. ORDERING's
  destructive R134 test covers it.
- `test_r8_check` has 20 tests (R8_VALIDATION's step-1 row says 19).

## Prototype check (scratch copies `seed/proto.kicad_pcb` and `seed/proto_a.kicad_pcb`, deleted after the pass)

Both trims applied, zones refilled with `pcbnew.ZONE_FILLER`, saved to the scratchpad only:
- DRC: 0 clearance, short, connectivity or rule items. The scratch folder lacked `kilib`, so only
  `lib_footprint_issues` appeared.
- `check_r8`: every check passes, rigid digests included; D18 is still 2.65 mm. Its one failure, "LS120: readable model
  smaller than 8.5 x 8.5 mm", is the missing `${KIPRJMOD}/kilib` 3D model in the scratch folder. `route_check
  --profile r8`: 0 failing, the same 3 allowlisted.
- ACT_FET_S (0.05 mm): R 0.18 mΩ, neck 4.97 mm, 21.4 °C (≤ 30 °C), unchanged.
- RAW_ACT at the 0.1 mm iteration grid, the same grid on both boards: board as built R 1.45 mΩ, neck 5.90 mm,
  17.6 °C (step 9's 0.05 mm qualification: 5.94 mm, 17.5 °C). Prototype with both trims: R 1.45 mΩ, neck 5.74 mm,
  18.2 °C, cut box (20.7, 23.2, 80.65, 85.65), i.e. at the optional C127 step (b). A second copy with trim (a) and the
  ACT_FET_S trim only (`proto_a`): R 1.45 mΩ, neck 5.90 mm, 17.6 °C, the as-built cut box (20.2, 21.8, 80.75, 86.25);
  DRC on it also has no clearance or connectivity item.
- RAW_ACT at the 0.05 mm qualification grid, both trims: R 1.45 mΩ, neck 5.72 mm, 18.3 °C, cut box (20.75, 23.2,
  80.65, 85.7), `neck OK` against D12's 20 °C (as built: 5.94 mm, 17.5 °C). So option (b) costs 0.22 mm of neck and
  0.8 °C.
- Spacings: ACT_FET_S to J124.1 1.089 mm; RAW_ACT to R127.1 1.115 mm and to C127.1 1.000 mm; rule E (1.30 mm) and the
  other pyro rule approaches unchanged.
