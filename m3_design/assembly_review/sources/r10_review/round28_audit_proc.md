# R10 round 28 fix pass: audit lane B (ORDERING §8 and the vehicle handoff)

Scope: every step a person carries out in `docs/ORDERING.md` §8 (8.1 to 8.4) and the procedures in
`docs/R10_VEHICLE_HANDOFF.md`, plus R28-TRI-05 and R28-TRI-09's ORDERING label. Target commit `19dd0b5`, board
`a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`.

**Board read.** I read a copy of the committed board (`git show HEAD:…/m3.kicad_pcb`, SHA-256 `a0ec075e…`) with KiCad
Python. I did not save or change any board file. The working-tree board changed while I worked: the CAD lane's build
was running. Its SHA-256 was `b3b4aac5…` mid-build, then `a0ec075e…`, then `bc50bce8…` at hand-back. All my figures
come from `a0ec075e…`.

**Other sources.**
- The netlist (pad nets from the board dump) and `pin_table.tsv`.
- The committed `m3-PTH.drl`.
- check_r10's M-6 courtyard function.
- The cached maker PDFs: TPS25947 p9, TPS2121 Table 9-1 p13, AP6320x DS41326 pp4–5, TPS7A91, ESD103 Rev 1.3 and
  TPS2553.
- `round23_safety_severity_check.md` and `round20_mcu.json` / `round20_power.md`.

Scratch scripts are in `.supervisor/r28_audit_proc/`. Nothing runs in the background. Labels below: **Calc** =
Calculation, **Inf** = Inference.

## Triage items

**R28-TRI-05 (ORDERING §8.3, QSPI_IO2 / PE4 bullet).**
- **Before:** "meter U3.3 (QSPI_IO2) to R127.1 (the PE4 gate network): it must read open".
- **After:** the board unpowered, the meter in resistance mode, both polarities:
  - an intact board reads above 0.9 kΩ, or open, both ways;
  - red lead on R127.1: about 0.91 kΩ to GND plus a diode drop through the GND-side input clamps of U1.1 and U3.3;
  - reversed: open or slowly rising, as the 3V3 capacitance charges;
  - a continuity beep, or under 100 Ω, in either polarity is an IO2-to-PE4 bridge: reject the board.
  - Labels: 0.91 kΩ is a Calc; the reading through the clamps is an Inf.
- **Derivation (netlist).**
  - QSPI_IO2 = {U1.1, U3.3}; PYRO1_GATE_N = {U1.3, R126.1, R127.1}.
  - R127 is 1 kΩ to GND; R126 (220 Ω) + R128 (10 kΩ) is 10.22 kΩ to GND. In parallel that is 910.9 Ω nominal, and
    901.8 Ω with 1 % parts, so the red-on-R127.1 reading is always above 0.9 kΩ.
  - Reversed, the path runs through the supply-side clamps, the 3V3 rail's capacitance and its loads. The 3V3 → D120
    → R131 → continuity divider path alone is 21.2 kΩ plus a diode. So that reading is open or rising, still above
    0.9 kΩ.
  - A bridge reads near 0 Ω both ways.
- **Two further changes, with reasons.**
  - The header now says "before first power and coating" (R23's recommended fix). The power-path bullet now says it
    comes after this check.
  - The figure sentence is made exact. It now reads "with the MCU driving IO2 high" (1.186–1.977 V is the MCU-driver
    row; the flash at its default 25 % drive gives 0.56–0.82 V). It also reads "fires the match after about 0.55 ms
    in all but one modelled corner" (R23's typical-FET, strong-N case gives only 45 mA).

**R28-TRI-09 (same bullet).**
- **Before:** "(`round23_safety_severity_check.md`, Calculation)".
- **After:** "(…; Calculation / Inference: the timing is a simulation, and the driver resistances, the flash drive,
  the AON7524 sub-amp curve and the match thermal model are inferred)". These are the source's "Coverage limits".

## Other steps changed (before → after, derivation)

| # | Where | Before → after | Derivation |
|---|---|---|---|
| 1 | §8 Status | "rounds 28 and 29 review it" → round 28's 9 real errors (one Major, an AGENTS §2.5 labelling error; 8 Minor; none on the board); the fix pass left the board unchanged; rounds 29 and 30 review it | Stale after this pass; the docs lane routed it here. "Board unchanged" assumes the CAD lane's final build reproduces `a0ec075e…` (root to confirm). |
| 2 | §8.1 tab table | J400 "3.15 mm", J410 / J122 "3.16 mm" → "3.155 mm" (as J440) | All four courtyards are 3.155 mm from the tab edge (J400 / J440 x 3.155; J410 / J122 x 42.845). |
| 3 | §8.2 C84 heat limit | "R166's courtyard is 0.56 mm away on the top" → "on the top R166's courtyard is 0.56 mm from C84's" | C84 courtyard y ≤ 83.795 and R166 courtyard y ≥ 84.355: 0.56 mm. C84's land to R166's courtyard is 0.855 mm, so the old wording was ambiguous. The five joints, 0.545 / 0.605 / 0.814 mm were reproduced. |
| 4 | §8.3 first-article power path | "measure the VLOGIC capacitance at TP83 … or the hold-up", with no pass value → measure TP83 (red) to GND, unpowered: about 0.41–0.62 mF with C84, about 0.04–0.05 mF without; pass at ≥ 0.3 mF (Calc). The hold-up option is compared with the battery-break figures (300.8 µF). The bullet now follows the unpowered QSPI meter check. | VLOGIC = C84 470 µF ±20 % (MA25V470**M**) + C6 / C7 22 µF ±20 % (CL21A226**M**) + C99 0.1 µF. That is 411–617 µF; without C84, 35–53 µF. The step had no criterion. |
| 5 | §8.3 power-knot | "8.7–13.3 mm away" → "8.7–13.4 mm away, centre to centre"; Calc / Inf labels on 1.2–2.2 W / 1.4–2.2 W (80–88 % efficiency and allocations); U400 "0.46 W at 1.56 A … ; Inference" | U401 B(27.6,13.6): L400 F(24.2,5.55) is 8.74 mm away, U400 F(16.9,5.55) 13.39 mm. The figures rest on allocations (round20_power). |
| 6 | §8.3 cold screen | Healthy / open ≈ 99.369 / 99.338 / 146.23 mV, unlabelled → "(nominal at 3V3 = 3.3 V and a 0.20 V BAT54 drop, parts_qualification; Calc / Inf)" | Reproduced: 3V3 − 0.20 V through D120 + R131 10 kΩ into 11.2 kΩ ∥ (11.2 kΩ + R134 + match); the source labels it "Calc / Inference". |
| 7 | §8.3 C87 turn-on / drop-out | "(Calculation …)" → "(Calculation / Inference …; C87's X7R bias allowance is an Inference …)" | The binding note uses 297 kΩ × 0.72 × 220 nF. With 0.15 µA of leakage, 1.401 → 1.116 V gives 10.3 ms ✓. The 0.72 factor is an Inf (docs lane's same-class sibling). |
| 8 | §8.3 J400 chatter | Duplicate "under flight-level vibration" removed; "Calculation" → "Calculation / Inference" (C87's X7R allowance) on the limits, the 1.095 / 1.028 / 1.025 V trains and the guidance fractions | Same EN model as #7. |
| 9 | §8.3 port faults | "PORT_4V8 rises about 44 ms or more before 3V3" → "can rise tens of ms before 3V3", with a labelled derivation (Calc / Inf) | 44 ms is VLOGIC's full slew to 7.4 V plus tSET (round20_mcu.json). 3V3 starts earlier: Table 9-1 scaled to 470 nF gives 166–196 V/s; AP63203 starts at 3.3–3.7 V (DS41326 p5) with a 4 ms soft-start, so 3V3 regulates 21–26 ms into the slew, after an unquantified settling time. "44 ms or more" was an unsupported lower bound. |
| 10 | §8.3 J400 ESD | Label and procedure changes, listed after this table. | Infineon ESD103 is rated ±10 kV contact at 150 pF / 330 Ω (Rev 1.3 p4), so an 8 kV test is inside its rating. TPS25947 p9 gives VUVLO(R) 1.183 / 1.20 / 1.223 V, VUVLO(F) 1.076 / 1.09 / 1.116 V and IENLKG ±0.1 µA. These reproduce 4.29–4.80 / 4.72–5.25 V (nominal 4.51 / 4.96 V), 5.553 / 6.493 / 7.433 V at 1 / 2 / 3 µA, and 1.223 V / 300 kΩ = 4.08 µA. The 7.5 / 9.6 V figures are labelled Inference in M3_R10:452. |
| 11 | §8.3 Q120 gate drive | "Probe ACT_GATE … and record the dummy-load drop across the bus", with no pass value → see the list after this table. | Gate: R119 ∥ R120 = 50 kΩ against R121 10 kΩ, so VGS ≈ −0.83 V_S. With both gate vias open, R120 / C120 hold VGS at 0. Intact drop: 2 × ≤ 12.3 mΩ (AONR21357 Rev 2.1 p2) × ≤ 2.4 A ≈ 0.06 V plus copper, well under 0.2 V. The body diode adds 0.7–1.0 V (R23's table). |
| 12 | Per-flight step 3 | "Confirm the powered BUS / CONT readings" (no band) → adds "(BUS at least 0.96 × the VLOGIC_SENSE-derived pack voltage, M3_R10 "Firmware" rule 4, with CONT about equal to BUS through the dummy)" | With PE4 low, CONT and BUS differ only by the continuity current (0.66 mA) across R134 plus the dummy (about 3 Ω), about 0.2 mV. D120 is reverse-biased. |
| 13 | Per-flight step 4 | "With J400 open, fit the e-match" → "With J400 open, and no USB and no self-powered module attached on any port (GPS, radio, AUX or camera), fit the e-match" | This is the R10 single-switch rule (AGENTS "Pad arming access"; the handoff). USB powers the logic with J400 open, so PC1 could live the bus from BAT_IN. The one numbered list omitted it. |
| 14 | §8.3 battery-break | "(Calculation from the trip window …)" → "(Calculation / Inference from the trip window …)" | The hold-up model's load and capacitance allocations; the docs lane's same-class sibling (AGENTS uses the same label). |
| 15 | Handoff status | "So rounds 28 and 29 review" → the round 28 result and rounds 29 and 30 | As #1. |
| 16 | Handoff chatter | "(Calculation, D-R25-01, D-R26-03)" → "(Calculation / Inference: C87's X7R bias allowance is an Inference; …)" | As #7; the docs lane's sibling. |
| 17 | Handoff supports | "The east edge carries 34 g of the board mass" → "… (Inference)" | M3_R10:975 labels the mass model as Inference. |

**#10, J400 ESD (§8.3), in full.**
- **Labels.**
  - The unclamped 7.5 / 9.6 V gets its basis, a 150 pF / 8 kV contact discharge, and an Inference label.
  - The (b) turn-off figures and the 4.08 µA figure get Calculation labels.
- **Procedure.**
  - **Before:** "First article, and after any field event …: a contact discharge at the switch screw in flight
    configuration, then the switch-off and J121.2 checks, and … a bench supply ramp".
  - **After, first article:** a 150 pF / 8 kV contact discharge at the switch screw, in flight configuration but with
    a 1–2 Ω dummy in J121 and no e-match (the §8.3 bench rule).
  - **After, at first article and after any field event:** the switch-off and J121.2 checks (per-flight steps 2 and 3,
    made without an e-match), then the turn-on / turn-off ramp with a bench supply on J1 and J400 closed.
- **Why.** "In flight configuration" let a person apply a deliberate ESD test with the e-match fitted, which breaks
  the §8.3 dummy-load rule. Without a level, the test could not be repeated. And the ramp needs J400 closed.

**#11, Q120 gate drive (§8.3), in full.**
- Before coating, with PC1 high and a dummy in J121, probe ACT_GATE at R120.2 / C120.2 against Q120's source at R120.1
  B(18.5,72.17).
  - Intact: |VGS| at least 4.5 V (the load-switch step).
  - A gate cut off from R121 sits at its source: VGS about 0 V.
- During the dummy-load fire, record BAT_IN − RAW_ACT (TP80 to TP120) with a differential probe, or with two channels
  referenced to GND at TP74 / TP88. Above 0.2 V fails (R23-SAFETY-05's own criterion, which was not carried into
  ORDERING).
- The four-stall currents get "Calculation / Inference on the fire budget".

## Steps verified correct, unchanged (by subsection)

| Subsection | Verified | What was checked |
|---|---|---|
| §8 preamble | 3 | All 10 moved-part positions in the header (C10, C11, R164, R173, D402, C88, R92, TP88, R402, R403); the compass (x 0 west, y 0 aft; north = smaller y); the terminal rows at x 7.4 / 38.6 |
| §8.1 table and order form | 7 rows + 15 fields | Vias: 309 = 304 × 0.5 / 0.3 + 4 × 0.6 / 0.3 + 1 × 1.0 / 0.5, with BAT_IN at (17.5,87.15). EN via (17.10,82.80); U9.1 to U9.5 is 0.200 mm. The Electrical-test screen logic (steps 2 and 3 both catch an open EN via). Minimum via 0.3 / 0.5 mm. |
| §8.1 export and supplier steps | 6 | `r10_fab.sh` uses `export_fab --pending` then `fab_manifest --bind`. The `jlc_stock` / `jlc_cost` / `check_procurement` flags (`--boards`, `--profile r10`) exist. Snapshot rows agree with the round 28 manufacturing and parts lenses (not re-queried). |
| §8.1 consignment and owner choices | 12 | Process text, not measurable. No conflict with AGENTS §2. |
| §8.1 tab plan, mark and VIPPO | 4 tabs + 4 windows + 1 + 4 | Tab bands against the courtyards. U401.11 vias (27.3,13.6) and (27.9,13.6) are GND 0.5 / 0.3. The committed `m3-PTH.drl` has T1 0.3 mm × 308 (2 + 306 others), T2 0.5 × 1, T3 0.6 × 4, T4 1.3 × 27. Paste overlap (0.3 − 0.22) / 2 = 0.04 mm. |
| §8.1.1 | 6 + 4 | Every figure reproduced: 6.932837 / 5.437970 W; 1.812657 / 2.265821 / 2.390393 / 2.987991 / 4.123602 / 5.154503 Ah; 1.733209 and 1.705 Ah; physics basis 0.6 / 0.75 Ah and 0.17–0.46 W. |
| §8.2 package, legends, remarks | 11 bullets | See the list after this table. |
| §8.2 terminal table and confirm list | 8 rows + 7 bullets | Terminal centres, rotations and pin nets. Port UART chains: J410.3 → R441 → PD8 (U1.55), J410.4 → R440 → PD9; J420 → PB13 / PB12; J440 → PC6 / PC7; J9 reversed through U12. All listed poses: Q120, Q121, Q124, C126 with its GND via (15.8,59.425), C123, C411, C421, C431, C91, C92, C84 (pad 1 VLOGIC), D9 (pad 1 RAW_PROTECTED cathode), U4, J430. L400 pads 2.0 × 1.8 mm at ±2.25 mm (2.50 gap, 6.50 overall). DFM courtyard edge gaps: R400 / R401 / R404 1.025, C403 1.955, C95 1.505, R166 1.755 mm; R92 2.525, TP88 2.555 mm. |
| §8.2 VCAP | 1 | C19 / C20 are CL10A225KO8NNNC. |
| §8.3 opening and order | 6 | Dummy-load and USB rules against AGENTS §2. J2 F(5,39.4) beside the (4,44.3) support. |
| §8.3 probe worksheet | 13 rows + 2 | Every face, coordinate and net (TP80 to TP88, R119.1 / R120.2 / C120.2, C24.1 / .2, C15.1, C88.1, C82.1). U9 pad 5 / 6 ends: pads y 80.4–82.8 against the body 80.5–82.7, so 0.10 mm is exposed. R84.1 is BAT_ILIM; R84 is 750 Ω. |
| §8.3 coating worksheet | 8 | See the list after this table. |
| §8.3 staking | 1 | C84 F(27.5,78.5); LS120 F(23,58.5). |
| §8.3 bench list (19 bullets; 9 changed above) | 10 | See the list after this table. |
| Per-flight checklist (7 steps; 2 changed) | 5 | See the list after this table. |
| Per-installation NRST | 1 | NRST = {C24.1, J2.3, U1.14}, with no external pull. Against RPU 30–50 kΩ, "≥ 0.90 × 3V3" means leakage ≥ 270–450 kΩ, so the 250 kΩ requirement always holds. A good board reads 0.995 on a 10 MΩ DMM. |
| Hot-plug; sensors | 2 | BAT_IN bleed R167 10 kΩ with C80 / C96 10 µF, C89 / C95 22 µF and C88: 64–70 µF, τ ≤ 0.71 s, 8.4 → 1 V in ≤ 1.52 s, so "≥ 2 s, TP80 < 1 V" holds. R166 (BAT_DAMP to GND) has no DC path in parallel. The IMU signs match M3_R10's axis map (U4 is west of the axis; centripetal acceleration east = −X_imu). |
| §8.4 | 11 rows + closing | See the list after this table. |
| Handoff | 10 procedures (2 relabelled above) | See the list after this table. |

**§8.2 package, legends and remarks, in detail.**
- All 13 bottom pin legends are on B.Silkscreen; J122 3:S3 is on the top.
- 14 parts have no Fab body: 5 with no mark and 9 with a pin-1 dot only.
- The C84 lands are at (27.5,75.25) and (27.5,81.75).
- The hand-solder list is complete at ≤ 2.171 mm, recomputed: the 1.762–2.171 mm range is R13 to U5.
- The J440 GND vias are 0.300 mm from J440.3 / J440.4.
- D402's M-6 courtyard gaps, 1.768 / 1.808 mm, were reproduced with check_r8's courtyard function.
- 27 contacts and 6 GND contacts.

**§8.3 coating worksheet, in detail.**
- Every selected part exists on the stated face; R62 and R63 are absent.
- The BAT_ENABLE vias are (17.1,82.8), (19.675,66.6) and (21.3,68.9). The (17.1,82.8) via is 0.200 mm from
  BAT_FAULT_N F.Cu.
- U5's body is x 8.1–13.1, y 47.6–50.6; its pads x 8.42–12.78, y 47.05–51.15.
- U4's courtyard plus silk is about x 15.1–19.1, y 44.3–47.5.
- C10's Fab / pad gap to U5's union is 3.016596 mm, reproduced.
- TP122's box is 1.40 mm from the U5 pads. Its "south / east", "north / west" wording is consistent with north =
  smaller y.

**§8.3 bench list, the 10 unchanged bullets.**
- Harness pin identity.
- Board temperature (C89 is a BAT_IN X5R part).
- Load-switch gate: 3.3 V × 2 / 3 = 2.2 V, or 2.19 V with VOH under the 1.1 mA divider load; (1 kΩ ∥ 2 kΩ) × 10 nF =
  6.7 µs; −0.833 V_S.
- Static / leakage.
- PC1 / PE4 modes.
- Boot: R5 is 10 kΩ from BOOT0 to GND; PA2 (U1.24) → R152 → J122.3.
- Power / thermal.
- USB-only: R85 66.5 kΩ; the J410.3 / J420.3 / J440.3 pins are the board TX lines.
- U401 X-ray.
- GNSS: 63 × 25 MHz = 1575.000 MHz, 0.42 MHz from L1.

**Per-flight checklist, the 5 unchanged steps.**
- Steps 1, 5 and 7.
- Step 2: Q120 / Q121 IDSS is ≤ 1 µA at 25 °C and ≤ 5 µA at TJ 55 °C (AONR21357 Rev 2.1 p2, at −30 V). Through the
  11.2 kΩ RAW_ACT bleed that gives ≤ 56 mV, below 0.1 V, within the ≤ 55 °C site limit (an observation below covers
  hotter bays).
- Step 3's "within 1 s": the C120 off τ is ≤ 129 ms and RAW_ACT's τ is under 1 ms.
- Step 6: Q120 pins 5–9 are BAT_IN.

**§8.4 rows and closing, in detail.**
- J400 dressing: J440.1 or J440.3 onto J400.2 gives 4.792 V or 3.3 V × 300 / 771, so EN sits at 1.866 / 1.284 V.
- About 7 µA through the contact: 8.4 V / 1.24 MΩ.
- Battery, J440 and terminal-lead routing.
- Wire arithmetic: 3.9 / 4.1 / 5.1 / 5.7–6.5 mm; the 4.493 mm bore figure recomputed.
- Five Edge.Cuts holes at Ø3.2 mm.
- L1 at B(25,74.6); 0.984175 mm.
- Chute landing load 98–163 g.
- Washer lands: LED2.2 3.808, LED1.1 3.860, J2.1 3.880 and J2.3 3.987 mm (GND, GND, 3V3, NRST).
- C32.2 is 4.536 mm from the support.

**Handoff, in detail.**
- The terminal table and its legends.
- J121's polarity.
- Port directions.
- USB-only and per-flight summaries (consistent with the changed steps).
- J440 routing.
- Supports and lands.
- Tail arithmetic: 3.80 − 1.60 = 2.20 mm; 1.80 mm.
- microSD at (24,24.3).
- The pack figures.
- The sled-pocket box contains C411 / C421 / C431.
- Boot.
- Cost (agrees with §8.1).

## Siblings in other files (for root; not edited)

1. **R28-TRI-05 / -09 wording.**
   - `m3_design/r10_sch_check.py:366` generates binding note :610. `tools/test_r10_check.py` asserts the phrase.
   - These carry the triage text, but not "with the board unpowered", "before first power", "with the MCU driving IO2
     high" or "in all but one modelled corner".
   - M3_R10 and FMEA:38 already match ORDERING (docs lane).
2. **Q120 first-article pass criterion** (|VGS| ≥ 4.5 V; BAT_IN − RAW_ACT ≤ 0.2 V).
   - M3_R10:1112 and `r10_sch_check.py:367` (rule 4) still say only "record the dummy-load drop".
3. **"PORT_4V8 rises about 44 ms or more before 3V3".**
   - Docs lane: M3_R10:1179 and REQUIREMENTS:64.
   - Audit lane A: `parts_qualification.md:102`.
   - CAD lane: `r10_sch_check.py:342`, which generates the binding note.
   - R10_VALIDATION:2637 already says "tens of ms (Inference)".
4. **"8.7–13.3 mm"** (13.39 mm centre to centre): R10_VALIDATION:2364, owner row 26. `round20_power.md` / `.json` are
   sealed.
5. **The cold-screen nominal label:** FMEA:9 quotes 99.369 / 99.338 / 146.23 mV with no Calculation / Inference
   label.
6. **Status lines "rounds 28 and 29":** `parts_qualification.md:13` (audit lane A).
7. **No sibling found** for the tab 3.155 mm, the C84 capacitance criterion (R10_VALIDATION:2647 and M3_R10:760 only
   point here), the R166 courtyard, the ESD dummy-load condition (M3_R10:460 only points here) or the per-flight
   step 4 precondition (AGENTS and the handoff already state it).

## Observations (no change)

- **Fire-current ratio.** "0.93–1.01× the 1.125 A floor … at least 1.39× / 1.04×" covers R23's whole case set,
  1.043–1.137 A (−20 °C and Q120's 0.04 Ω removed). Round 27 ruled it conservative, not false (R27-MCU obs 5).
- **R85's footprint description** says "351.2..448.7mA". ORDERING, M3_R10 and R10_VALIDATION use 0.3477–0.4530 A.
  This is board-file text, not mine.
- **Per-flight step 2 above the 55 °C site limit.** AONR21357 IDSS is specified only to TJ 55 °C (≤ 5 µA). In a
  hotter bay, the J121.2 < 0.1 V margin is not established. A false reading there refuses the e-match, which is
  fail-safe (Inference). §8.3 keeps the site at ≤ 55 °C bay air until the board-temperature test passes.
- **§5 (R9) bench tests.** §8.3 adopts "generic" §5 tests. §5's "armed, MCU held in reset" variants cannot arm R10's
  bus, because PC1 is low in reset. The R10 bullet says to use the flight firmware, so it does not apply them as
  written.

## Not done or not verified

- **The board.** The status lines assume the CAD lane's build reproduces `a0ec075e…`. The working tree read
  `bc50bce8…` mid-build at hand-back.
- **The fab package.** The working-tree manifest, Gerber zip and PDFs were re-exported, so §8.2's "the round 26 fix
  pass's build results" may need re-binding by root.
- **No re-runs.** I did not re-run the supplier queries, DRC, check.sh, the EN, hold-up or fire models, or any
  physical test.
