# R8 review pass 2: pyro and arming safety

Reviewer: independent, read-only (no repository file changed but this report; the board and schematic were never
saved). Board `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`6600ef9462b37ec58540e0dd7edd97577c3e778bda0d233d3c1dffc555ad5a8d` (confirmed before and after the review; `git status`
identical before and after). Netlist `schematic.net.xml` `0cc1ed692fb99dd2…` (unchanged). Baseline R7 `c872a3d3…`,
extracted read-only with `git show 431025d:…/m3.kicad_pcb` into the session scratchpad; `../rocket-flight-computer-r7`
and `-r6` were not touched.

**Verdict: 0 Critical, 0 Major, 4 Minor** (three cheap ones marked worth fixing). Every pass-1 finding in this dimension
is closed or properly dispositioned: ACT_FET_S is now 1.089 mm from J124.1 (gated by the new `check_r8.battery_pyro`),
RAW_ACT is 1.115 mm from bare R127.1, and the records carry BAT_ENABLE's crossing. The arming break is complete in the
netlist and in copper. The gate is defined off in reset and unpowered. Every `m3.kicad_dru` pyro rule is loaded (seeded
DRC) and met. `check_actuators` holds, D18 (2.65 mm) and D19 (5.89 mm) hold, and A8 is unchanged. Fix pass 1 added no
net near the armed copper. The four Minors:
- the new `battery_pyro` gate guards BUS / IGN but not the drain PYRO1_OUT. Battery copper on the drain is the worse
  case: it fires with the link in and the switch open. The copper is fine (3.56 mm); the gate has a gap (R8P2-PYRO-01);
- M3_R8 calls GND next to armed copper "the safe direction". For PYRO1_OUT it is the firing direction, and step 7 put
  two tented GND vias 0.53 mm from drain copper (R8P2-PYRO-02);
- the bootloader-jump binding constraint does not ask for PE4 low (R8P2-PYRO-03);
- fix pass 1's ACT_GATE chamfer passes 0.264 mm from bare C120.1. A bridge there fails safe (R8P2-PYRO-04).

Labels: **Measured** = pcbnew on the board above (scripts in the session scratchpad `p2pyro/`: `measure.py`, `rules.py`,
`d18.py`, `outn.py`, `gndvias.py`, `under.py`, `oldgate.py`, `refill.py`); **Datasheet** = cited maker document;
**Inference** = reasoning not measured (AGENTS §2.5).

## 0. Previous findings in this dimension (pass 1, board `429b6db4…`)

| Pass-1 item | Disposition (R8_VALIDATION "Review pass 1", D85) | Verified on `6600ef94…` | Status |
|---|---|---|---|
| R8P1-PYRO-01 ACT_FET_S pour 0.501 mm from J124.1 | `r8_power.py` R8_ACT_FET_S_B corner (11.4, 97.6) → (12.4, 97.6); gate `check_r8.battery_pyro` + seeded test | **Measured** 1.089 mm (`0.501`→`1.089 PYRO1_BUS ACT_FET_S B.Cu J124.1 / zone R8_ACT_FET_S_B`); `battery_pyro` nearest 1.089 mm in check_r8's report; `test_r8_check` 23 OK. The 0.301 mm to the tented ARM1_SENSE via (14.55, 97.55) is kept, with a recorded reason (sense node, no fire path, 0.2 mm of neck) | Closed (but see R8P2-PYRO-01: the gate's scope) |
| R8P1-PYRO-02 RAW_ACT pour 0.696 mm from bare R127.1, 0.501 from C127.1 | (a) chamfer (21.3, 87.3), (20.6, 88.0); (b) not applied, recorded (benign, 0.22 mm of neck) | **Measured** R127.1 1.115 mm; C127.1 0.501 mm (rule A, masked pour, RAW_ACT–CONT does not fire) | Closed / properly dispositioned |
| R8P1-PYRO-03 BAT_ENABLE through the block; survey missed sense / gate neighbours | records: M3_R8 sentence corrected (l.297–302), R8_VALIDATION "Pyro review observations" table, ORDERING §5 switch-cycle and H-6(b) steps | M3_R8 now says "One signal net still crosses the block"; the observations table carries each neighbour with its fail-safe direction; ORDERING l.156 and l.159 carry "the board must turn off with the link in" and "RAW_ACT dead and the board off … link out and again with it in" | Closed |
| R8P1-PYRO-04 GATE_N lane between the sense lanes (hard short ≈ 0.37 V) | recorded; ORDERING static gate repeated warm | ORDERING l.154: "repeat once on a warm board where convenient … R8P1-PYRO-04"; geometry unchanged (GATE_N–ARM1_SENSE via 0.220 mm, GATE_N–CONT 0.300 mm) | Properly dispositioned |
| R8P1-REQUIREMENTS-04 (pyro part: the BAT_ENABLE latch) | as PYRO-03 | as above | Closed |

## 1. Gate runs (this pass)

| Run | Result |
|---|---|
| `tools/check.sh` (unchanged board) | exit 0: DRC 0 at every severity, unconnected 0, parity 0, ERC 0; audit OK; silk 0; `R8 CAD contract: OK`; route_check r8 0 failing / 3 allowlisted / 0 stale / 0 out-of-date no-GND reasons; `actuator safety contract: OK`; fit OK |
| check_r8 evidence | `battery_pyro` nearest 1.089 mm (ACT_FET_S to J124.1, B.Cu); `inner_power_pyro` 2.65 mm (BAT_IN In2 to R134.1); `gate_servo` none under 0.5 mm on the 8 listed layer pairs; `inner_signal` In2_rigid_exempt 3.4 mm (D70); rigid `ch1_parts` / `ch1_copper` / `pyro_block_area` digests equal R7's |
| `tools/test_r8_check.py` | 23 tests OK (including the D85 seeded test) |
| Seeded DRC (scratch copy `p2pyro/seed/`, deleted) | a RAW_ACT track 0.75 mm from J124.1 gives `Clearance violation (rule 'Pyro E: RAW_ACT to bus and igniter (ARM break)' clearance 1.0000 mm; actual 0.7500 mm)`; a via on drain copper beside the GND pour gives `rule 'Pyro D: GND to bus, igniter and drain' clearance 0.5000 mm; actual 0.4898 mm`. kicad-cli loads the custom rules |
| `m3.kicad_dru`, `check_actuators.py`, `m3.kicad_pro` | `git diff 431025d` empty for all three; DRU SHA-256 `1674d58b…` = `check_actuators.DRU_SHA`; check_actuators `5de1eb3c…` = `check_r8.CHECK_ACTUATORS_SHA` |
| `pyro.kicad_sch`, `actuator_power.kicad_sch`, `battery_entry.kicad_sch` | differ from 431025d only in `(rev "M3-ASSY-R8")` |
| Zone fills | a native `ZONE_FILLER` refill in memory gives the saved fills exactly (14 zone/layer fill sets, 0 differences): every measurement below is on current fills |

## 2. Arming break (AGENTS §2.1, §2.2; F8)

- **Netlist** (check_actuators rules 1–3, pad level, and `schematic.net.xml`): PYRO1_BUS = {J124.1, R132.1, R134.2};
  PYRO1_IGN = {J121.2, R134.1}; J124.2 is RAW_ACT; RAW_ACT is Q121's drain (Q120's drain on BAT_IN); no test point on
  BUS / IGN / OUT; no pyro terminal pin on BAT_IN. Unchanged from pass 1 and R7.
- **Copper:** DRC 0 (no short, no unconnected item). Rule E's closest is 1.300 mm (the RAW_ACT F.Cu and B.Cu pours to
  J124.1). Battery-live copper on the same layer as BUS / IGN is ≥ 1.089 mm (ACT_FET_S, B.Cu). On the inner layers the
  rasters under every CH1 pad (+0.5 mm, 0.1 mm grid) show only GND, antipad voids, each pad's own net and block-internal
  pyro vias. RAW_ACT is only under J124.2, its own pad (Measured, `under.py`).
- **Nothing bypasses J124.** With the link out, every path into the igniter is a 10 kΩ-class divider or pull-up
  (≤ 0.14 mA from the cold pull-up, ≤ 0.2 mA from a sense pin driven high; pass-1 arithmetic, unchanged netlist,
  Inference). This is far below the MJG Firewire's 0.30 A no-fire current (MARGIN_PRESCRIPTION l.74).

## 3. Gate defined off (AGENTS §2.4; F6, F8)

Unchanged netlist and values, all pinned by check_actuators 4 / 4b / 4c (R126 220 Ω, R127 1 kΩ at the MCU side,
R128 10 kΩ and C126 220 nF gate to source, AON7524 pinned C431195). U1.3 = PE4. Its neighbours U1.2 / U1.4 / U1.5 are
no-net sentinels (rule 5). PE4 is not among the ROM bootloader's driven pins (binding note constraint 9). The binding
note keeps "Lock PE4 (GPIOE_LCKR) before any other GPIOE set-up; SPI4 is never enabled". AON7524 V_GS(th) min 0.4 V,
I_GSS ±10 µA (AOS AON7524 datasheet, p. 2, https://www.aosmd.com/res/datasheets/AON7524.pdf). I_GSS × 1.09 kΩ is about
11 mV (Inference, as pass 1). One gap in the firmware-jump contract: R8P2-PYRO-03.

## 4. `m3.kicad_dru` pyro rules and the check_actuators contract

The DRU is R7's, unchanged and pinned. KiCad applies the last matching rule. After rule H come only a thermal-relief
rule (no clearance), "RAW_ACT pins to pours" (RAW_ACT THT pads to GND zones, a pair no pyro rule names) and the J2
Tag-Connect rule (J2 carries no pyro net and is far from the block). None lowers a pyro rule. Closest approach per
rule, conditions transcribed from the DRU (Measured, `rules.py`, same layer, pads / tracks / via rings / fills):

| Rule | Min | R8 closest (pass 2) | Where | Pass 1 / R7 |
|---|---:|---:|---|---|
| A RAW_ACT to gate / sense / mid | 0.5 | 0.501 | RAW_ACT B.Cu box to the PYRO1_CONT lane (B.Cu); F.Cu pour to C127.1. The gate pair: R127.1 1.115 | 0.501 / 0.95 |
| B bus / igniter / drain to gate | 0.5 | 0.670 | Q124.5 to the PYRO1_GATE track (block-internal) | same |
| C bus / igniter / drain to sense | 0.3 | 0.377 | PYRO1_BUS track to R132.2 (block-internal) | same |
| D GND to bus / igniter / drain | 0.5 | 0.500–0.501 | pours to J124.1, J121.1 / .2, Q124.5, R131.1, R173.1 | same / R7 same |
| E RAW_ACT to bus / igniter | 1.0 | 1.300 | F.Cu and B.Cu pours to J124.1 | same / 1.001 |
| F bus / igniter / drain to other live | 0.5 | 0.700 | BAT_ENABLE track to R134.1 / R134.2 (masked) | 0.501 (ACT_FET_S, now 1.089) |
| G gate in the block to other live | 0.3 | 0.300 | GATE_N lane (x 18.75, B.Cu, the segment reaching y 87.78) to the PYRO1_CONT lane | same (PYRO-04) |
| A2 RAW_ACT to RAW_ACT_SENSE | 0.3 | none within 0.9 mm (R177's own pads 0.294, one part) | | same |
| H live pads to sense / gate pads | 1.0 | 1.025 | Q124.5 to R129.2 | same |

check_actuators passes on the board: rule texts, minima, nets and per-rule hashes, PYRO_BLOCK rectangle, pinned parts,
ACT_NETS.

## 5. D18, D19, D20 (independent)

- **D18** (In1 / In2 copper of every non-GND net, in plan view, against BUS / IGN / OUT copper on any layer; J124's pads
  exempt): BAT_IN In2 zone 2.650 mm to R134.1, RAW_ACT In2 west 3.260 mm, ACT_GATE via 2.790 mm, BAT_ENABLE via 3.178 mm.
  ACT_FET_S has no inner copper within 5 mm. Pyro-family inner items aside, these are the ARM1_SENSE In2 link (D70: under
  the BUS track, In1 GND between), the PYRO1_CONT exit via 0.715 mm and the TP122 via 1.250 mm. Met.
- **D19** (every layer pair): PYRO1_GATE_N's nearest servo PWM copper is 5.890 mm (B.Cu lane to J122.1). Met.
- **D20:** only the rigid 3.4 mm ARM1_SENSE In2 link (D70).

## 6. New copper near armed and pyro-control copper since pass 1, and its fail-safe direction

- **Armed copper** (BUS / IGN / OUT, any layer, within 3 mm; Measured): the same 7 non-pyro nets as pass 1. Only
  ACT_FET_S moved, from 0.501 to 1.089 mm. Every other figure is unchanged: BAT_ENABLE 0.700, RAW_ACT 1.300,
  BAT_OVLO 1.922, RAW_PROTECTED 1.975, BAT_DAMP 2.450, ACT_GATE via 2.521 mm. Fix pass 1 added no net near armed copper.
- **The drain PYRO1_OUT, every non-GND net within 6 mm** (Measured, `outn.py`): its own divider / cold pull-up / FET pads,
  PYRO1_CONT's exit via 0.715, BAT_OVLO 1.922 (R82.2, bare to bare, B.Cu), BAT_ENABLE 2.720 (R81.1), RAW_ACT 3.166 (plan) /
  3.669 (same layer), 3V3 3.428 (D120.3, the cold pull-up's own anode), **BAT_IN 3.562 (R82.1 to J121.1, bare to bare,
  B.Cu)**. Nothing low-impedance sits near the drain except GND at rule D. Fire directions: R8P2-PYRO-01 and -02.
- **Fix-pass-1 copper near the control nets** (Measured): the RAW_ACT F.Cu chamfer (R127.1 1.115 mm) and the ACT_FET_S
  chamfer (above); ACT_GATE's chamfered stub (D91), now 0.264 mm from bare C120.1 (ACT_FET_S), which fails safe
  (R8P2-PYRO-04). BUZZ_DRV (lane y 60.45) and PULLPIN cross over the B.Cu pyro corridor on F.Cu, with In1 GND and the
  In2 GND notch between. On the same layer, BUZZ_DRV is 0.900 mm from GATE_N's via and PULLPIN 1.400 mm. HSE_OUT's new
  via (24.69, 47.5) is ≥ 4.6 mm from the MCU-side sense vias. The tab move (D93) changes no copper. C128 (drain
  capacitor; a cracked C128 shorts the drain to GND, i.e. fires, R5-V06) is ≥ 18 mm from every tab.
- **Inherited near-pairs re-measured, unchanged:** GATE_N via (18.75, 54.3) 0.220 mm to ARM1_SENSE and 0.450 mm to In2
  3V3 (R7: 0.25 mm); ARM1_SENSE 0.216 mm to BAT_ENABLE (R175.2); ACT_FET_S 0.301 mm to the ARM1_SENSE via; the ACT_GATE via
  (13.48, 107.16) 0.380 mm to the RAW_ACT F.Cu pour and 0.301 mm to In2 BAT_IN (R7's ACT_GATE via: 0.301 / 0.301 mm, so
  not new in kind). All are recorded in M3_R8 / R8_VALIDATION or are R7's class.

## 7. Coating and leakage

- Bare gate to bare bus / igniter copper: 1.027 (R126.2–R134.2) and 1.491 mm (C126.1–R134.1), the rigid block, = R7. No
  bare 3V3 / RAW_ACT / always-live pad within 5 mm of a pyro gate pad except the block's own copper (Measured,
  `bare_gate`).
- TP122 (bottom, bare PYRO1_GATE, coated last): GND 1.001, ARM1_SENSE via 1.260, RAW_ACT pour 3.200, GATE_N 3.220 mm.
  TP121 (ACT_GATE, top, uncoated per ORDERING): GND and RAW_ACT pours 1.001 mm (masked), R121.2 1.330 mm. Unchanged.
- The coating list (ORDERING §5) and the leakage / static / plug-out cold gates are unchanged and still cover the block.
  The PYRO_BLOCK rectangle covers the step-7 GND vias next to the drain (R8P2-PYRO-02).

## 8. A8 (TP122's in-pad PYRO1_GATE via)

Re-measured: TP122 (20.45, 92.4), bottom, Ø1.5 mm; via 0.6 / 0.3 mm at its centre (locked), hole edge 0.60 mm inside
the pad edge; nearest GND vias 2.717 mm (22.875, 93.625), 3.665 and 3.761 mm; nearest foreign copper 1.001 mm (GND_B).
`route_check` reports 0 out-of-date no-GND reasons. Unchanged; the allowlist reason holds.

## 9. Findings

### R8P2-PYRO-01 (Minor, worth fixing): `battery_pyro` leaves out the drain, the one place where battery copper fires an armed igniter by itself

- **Requirement:** AGENTS §2.1 / §2.2 and F8 ("nothing fires … while armed with the MCU unpowered"; the links may be
  fitted with "the power switch as the pad arming device", FMEA H-6(b)); D85's intent (battery-live copper keeps rule
  E's margin from armed copper).
- **Finding:** `tools/check_r8.py` l.105–107 sets `BATTERY_LIVE = ('BAT_IN', 'ACT_FET_S')` and
  `ARM_SIDE = ('PYRO1_BUS', 'PYRO1_IGN')`, so the D85 gate (l.677–693) never measures BAT_IN / ACT_FET_S against
  PYRO1_OUT, which only rule F's 0.5 mm covers. Rule E rightly excludes OUT for RAW_ACT: RAW_ACT on the drain closes a
  loop at one potential. Battery copper on the drain does not. With the link in and the power switch open (H-6(b)'s
  normal pre-arm state, RAW_ACT dead), a BAT_IN / ACT_FET_S contact on PYRO1_OUT drives current down OUT → igniter → IGN →
  R134 → BUS → link → RAW_ACT. RAW_ACT's load is C121 (470 µF), the servos and the R177 / R124 divider, so no Q124 turn-on
  is needed. About 8.4 V / (2 Ω + 1–2 Ω) gives a peak of about 2.4 A, decaying with τ ≈ 3.5 Ω × 470 µF ≈ 1.6 ms. That is
  above the MJG Firewire's 0.60 A minimum all-fire for about 2 ms (MARGIN_PRESCRIPTION l.74). The servos' supply current
  then keeps flowing through the bridgewire (Inference; whether the first pulse alone fires depends on the bridgewire's
  time constant). The same contact on BUS / IGN, which the gate does guard, needs Q124 on as well.
- **Evidence (Measured):** today's copper has margin: the nearest BAT_IN to PYRO1_OUT is 3.562 mm (R82.1 to J121.1's ring,
  bare to bare, B.Cu, and in plan view), and no ACT_FET_S copper lies within 6 mm of any OUT copper (`outn.py`). So this
  is a gate-scope gap, not a copper defect. D85 and M3_R8 l.290–291 state the rule as "from PYRO1_BUS / IGN".
- **Fix:** add `'PYRO1_OUT'` to the set `battery_pyro` measures (for example
  `ARM_SIDE = ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT')`). Add a seeded case to
  `test_battery_live_copper_keeps_1_mm_from_the_bus_and_igniter` (a BAT_IN pour 0.5 mm from a J121.1 pad fires), and say
  "bus, igniter and drain" in D85 / M3_R8. The board passes unchanged: nearest 1.089 mm (ACT_FET_S–J124.1), drain
  3.562 mm.

### R8P2-PYRO-02 (Minor, worth fixing, records): GND next to the drain is the firing direction, not "the safe direction"; step 7 put two GND vias 0.53 mm from drain copper

- **Requirement:** AGENTS §2.5 and §3 (records state what was verified, inferences labelled); r8_plan step 9 ("pyro
  exits, coating, leakage"); D9 / D15 (the R4-qualified block carries over).
- **Finding:** M3_R8 l.329–330 says: "40 GND vias lie in the PYRO_BLOCK area … A leak to GND pulls a gate or sense node
  low or loads an armed bus: the safe direction." That holds for gate, sense, BUS and IGN, but not for PYRO1_OUT. GND on
  the drain bypasses Q124. With the link in and the switch on, the arming loop closes through the igniter
  (CIRCUIT_REVIEW l.39: the loop "closes the instant the plug is inserted"; rule D exists for exactly this). A resistive
  leak of about 24 Ω or less passes the MJG Firewire's 0.30 A no-fire current through the bridgewire (MARGIN_PRESCRIPTION
  l.74; 8.4 V across R134 2 Ω + a 1.5 Ω igniter + the leak, Inference). Step 7's legality model (D62) holds its vias at rule D's 0.5 mm from every pyro net.
  It placed GND vias beside the drain that R7 did not have: R7's nearest GND via to drain copper was 1.054 mm (Q124's own
  source via (25.45, 89.275), rigid).
- **Evidence (Measured, `gndvias.py`, both boards):** R8 GND via (30.85, 91.5), 0.5 / 0.3 mm, tented both faces:
  0.528 mm from the PYRO1_OUT track (30.58, 90.00)–(31.38, 90.80) w0.20. GND via (31.65, 87.3), tented: 0.537 mm from bare
  R173.1 (PYRO1_OUT, (30.58, 87.35)). The GND pours already stand at 0.500–0.501 mm from bare Q124.5, R131.1, R173.1 and
  J121.1 on R7 and R8 alike, so the closest approach and the bridge class (masked GND copper beside bare drain copper) are
  not new. New are a tented via ring as the neighbour, and a record that names the wrong direction. The plug-out cold test
  (FMEA H-1: a shorted FET or drain-to-GND path reads 0 mV) and ORDERING's static gate detect a hard OUT–GND path before
  any real igniter. R8_VALIDATION's observations table has no GND row.
- **Fix:** correct M3_R8 l.329–330, for example: "GND copper beside BUS / IGN and the gate / sense nets fails safe; beside
  PYRO1_OUT it bypasses Q124 and fires an armed igniter. It stands at rule D's 0.50 mm from bare drain pads, as in R7,
  and since step 7 two tented GND vias are 0.528 / 0.537 mm from drain copper ((30.85, 91.5), (31.65, 87.3)); the
  plug-out cold test and the static gate detect a drain-to-GND path." Add the row to R8_VALIDATION's pyro observations.
  Optional, no safety gain because the pour edge stays at 0.5 mm: let `make_ground.legal()` keep its vias 1.0 mm from
  PYRO1_OUT copper.

### R8P2-PYRO-03 (Minor, worth fixing, records): the bootloader-jump binding constraint does not put PE4 low

- **Requirement:** F8 ("nothing fires … while armed with the MCU … in reset, booting or idle"); AGENTS §2.4.
- **Finding:** fix pass 1 added constraint 11 to `step9/r8_binding_note.json` (`binding_note.py` l.50; D6.8): before a
  jump to the ROM bootloader, sleep the SX1262, drive PE9 low and return it to analog (or reset GPIOE). It is based on the
  fact that the bootloader configures only its own pins, so other pins keep their last application state (AN2606 Rev 70
  Table 135, as the constraint cites). The same holds for PE4, the pyro gate drive. The constraint's main branch changes
  only PE9. GPIOE_LCKR (constraint 1) freezes PE4's configuration registers, not its output data (RM0433 §11.4.8,
  GPIOx_LCKR: "each lock bit freezes a specific configuration register (control and alternate function registers)";
  ODR / BSRR are not among them. This is the reviewer's reading of the manual, not checked on the bench). So a
  jump made with PE4 high, which takes a firmware fault, would hold an armed gate on for as long as the bootloader runs:
  the 20 ms fire limit lives in the application (Inference).
- **Evidence:** constraint text: "put the SX1262 to sleep, drive RADIO_NRST (PE9) low, then return PE9 to analog mode
  (or reset GPIOE through RCC_AHB4RSTR)". No clause names PE4 / PYRO1_GATE_N. Board: U1.3 = PYRO1_GATE_N, R127 1 kΩ
  pull-down (check_actuators 4). In analog / reset state the pull-down holds the gate off (§3).
- **Fix:** in `binding_note.py` constraint 11, add "drive PE4 (PYRO1_GATE_N) low first, or reset GPIOE through
  RCC_AHB4RSTR, which also returns PE4 to analog so R127 holds the gate off", regenerate the note, and add the same words to
  D6.8 / F10's sentence.

### R8P2-PYRO-04 (Minor, not worth fixing): ACT_GATE's chamfered stub passes 0.264 mm from bare C120.1 (ACT_FET_S)

- **Finding:** D91 redrew ACT_GATE's Q121.4 stub (`r8_power.py` l.127) from the square corner (10.9, 107.16) to the 45°
  run (10.9, 105.56) → (12.5, 107.16). The B.Cu track now passes 0.264 mm from bare C120.1 (ACT_FET_S, 0.8 × 0.9 mm pad at
  (12.5, 105.76)), against 0.875 mm for the old path (Measured, `oldgate.py`). A bridge shorts the actuator switch's gate
  to its source. V_GS goes to 0, so the switch is held off: the safe direction for inadvertent ignition (check_actuators
  8b's reasoning for C120). It would cost the servos and the primary channel if it happened. C120's own pads already put
  the same pair 0.50 mm apart, bare to bare, by design. The track is masked. M3_R8's ACT_GATE paragraph ("C120 / R120 …
  0.63–1.30 mm by design") covers bare copper only, so the new gap is not recorded.
- **Why not worth fixing:** the bridge direction is fail-safe, the track is under mask, and the pair already exists at
  0.5 mm bare to bare. If the stub is touched again, a shorter chamfer from (10.9, 106.2) to (11.86, 107.16) keeps
  0.717 mm from C120.1. It is 3.30 mm against the 2.92 mm direct path (1.13×, +0.38 mm), within route_check's chain-detour
  tolerance as D91 quotes it (1.25× / 0.5 mm; Inference that the test reads it that way). Record the 0.264 mm in R8_VALIDATION
  part C.

## 10. Observations (no finding)

- Rule G is met at exactly 0.300 mm (GATE_N–CONT lane) and rule A at 0.501 mm (RAW_ACT B.Cu box–CONT lane), as in pass 1.
  A CONT short self-limits (PYRO-04's analysis).
- J124's "2:RAW" legend is 6.21 mm from J124.2 and 6.69 mm from J123.1 (PULL). It passes `terminal_legends`' "nearest
  own pin" strictly and reads correctly on `r8_top.png` (beside C121, over J124's west half). Legend placement is the
  requirements reviewer's to judge.
- The check_r8 `gate_servo` evidence lists 8 layer pairs; D19's independent all-pairs figure is 5.89 mm, so the
  restriction costs nothing.
- Scratch: `p2pyro/seed/` (one board copy) and `p2pyro/r7.kicad_pcb` were deleted after the pass; only small scripts
  remain in `p2pyro/`.
