# R10 round 26 triage (verifier)

- **Target:** commit `3d8e845`, board SHA-256 `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f`, checked
  before and after (unchanged).
- **Method:** read-only. Probes and outputs are in `.supervisor/r26_triage/`. I applied the round 26 review brief's
  definition of a real error.

**Totals.** I reproduced all 14 raw lens findings: safety 4, power 2, routing 3, mechanics 1, manufacturing 2,
requirements 2. Mcu, gate, parts and docs_binding had none.
- They merge into 12 real errors: **0 Critical, 0 Major, 12 Minor**.
- One fix changes the board: R26-TRI-09, two GND vias at J440.
- Of the 110 lens observations, safety 2 and 8 fold into findings and routing 7 is promoted. The other 107 stay
  observations (24 entries in the JSON).
- 0 findings were not reproducible.

## Real errors

| ID | Merged | Kind | What is wrong (key number) | Board change |
|---|---|---|---|---|
| R26-TRI-01 | SAFETY-01 | doc | Two statements are false. §1's "None of the pairs below fires the match by itself" fails for PYRO1_OUT to 3V3 (R173.1–D120.3, 0.5135 mm) and to 3V3A (R164.2, 0.5662 mm), and for the J440.1 / J440.2 harness row. Owner row 2's "Firing still needs a second fault at Q124" fails for those pairs and for the OUT–GND residuals (0.177 / 0.180 mm) that row 2 lists itself | no |
| R26-TRI-02 | POWER-02, SAFETY-02, REQUIREMENTS-01 | calc | "The fire budget's four-stall BAT_IN of 5.73 V" predates the AUX allowance. The bound budget gives 5.713 V, where the single drop-out is 8.07 ms (not 8.2), the window limit 7.50 ms (not 7.63), the margin 0.50 ms (not 0.63) and the fast-chatter fraction 19.7 % (not 20.0). The bench run should be at 5.71 V | no |
| R26-TRI-03 | POWER-01, safety obs 2 | calc | The "4000-train search kept EN ≥ 1.1173 V" result is a sample, not the worst case. One block per 100 ms reaches 1.1162 V at 7.62 ms, and 1.1168 V on the search's own 0.1 ms grid | no |
| R26-TRI-04 | SAFETY-03 | calc | The "5.37 V four-stall-plus-fire corner" counts the fire current twice. The corner is 5.71 V with a healthy match, 5.55–5.56 V with the match shorted and 5.50 V with match and leads shorted. No rule changes | no |
| R26-TRI-05 | SAFETY-04 | doc | U11.5 is OV1 (TPS2121 VQFN-HR pin 5), not "OV2" | no |
| R26-TRI-06 | REQUIREMENTS-02, safety obs 8 | doc | F4's "pack ≥ 5.96 V under four stalls" option rests on the single-drop-out rule that F6 replaces. At 5.96 V, 8 ms open every 50 ms takes EN to 1.088 V and trips U9 | no |
| R26-TRI-07 | ROUTING-01, routing obs 7 | doc | Owner row 8's counts are stale. There are five 0603 under-body vias, not six (R403's went with D-R24-09). The §6 table it cites lists 22 detour nets, not "ten" | no |
| R26-TRI-08 | ROUTING-02 | calc | "12 of the 21 are beyond 4 mm" is 13 (CAM_MCU_RX at 4.02 mm) by the metric that gives the sentence's other figures | no |
| R26-TRI-09 | ROUTING-03 | rule (+gate) | AUX_TX_WIRE and AUX_RX_WIRE change layer at J440.3 / J440.4 with the nearest GND via 3.900 / 4.037 mm away, against D-R19-15. route_check checks vias only and passes the board | **yes** |
| R26-TRI-10 | MECHANICS-01 | doc | R10_VALIDATION line 2752 gives 4.503 mm; the figure is 4.493 mm | no |
| R26-TRI-11 | MANUFACTURING-01 | doc | The C84 heat-limit list names the wrong joints. C9.1 is 0.545 mm away, not under a land; L1.1 and C7.1 overlap the lands; C8 (0.605 mm) is missing | no |
| R26-TRI-12 | MANUFACTURING-02 | doc | The J3 slot hand-finish neighbours omit R7 (2.010 mm), which is nearer than R8 (2.145 mm) | no |

Full evidence and the exact replacement text are in `round26_triage.json`.

## R26-TRI-01 (R26-SAFETY-01): severity settled from the circuit and the procedure

### The circuit (board netlist)

- **Fire path:** RAW_ACT → R134 2 Ω → J121.2 → match → J121.1 = PYRO1_OUT → Q124 drain.
- **Cold pull-up:** 3V3 → D120 (BAT54A, anode on pin 3) → R131 10 kΩ → PYRO1_OUT.
- **Sense dividers:** CONT and BUS are both 11.2 kΩ (5.1 k + 5.1 k over 2 k ∥ 2 k).
- **3V3A** is fed from 3V3 through R164 (2.2 Ω).

### Gaps (pcbnew, B.Cu)

- R173.1 to D120.3: 0.5135 mm.
- The PYRO1_OUT diagonal (15.5,56.6)–(16.87,57.97) to R164.2: 0.5662 mm (to the pad's rounded corner).
- Other neighbours of PYRO1_OUT:
  - GND: 0.1768 / 0.1800 mm (disclosed).
  - A 3V3 via (9.2,52.98) on F.Cu: 0.620 mm. This is the same class, outside the inventory's 0.5 mm band.
  - BUZZ_G: 0.510 mm. A bridge there carries only mA, so it cannot fire.

### When PC1 is high with the real e-match

1. Per-flight step 5 closes J400 on the rail with the e-match in.
2. The board powers up, waits at least 1 s and runs the cold screen (rule 2).
3. Firmware then raises PC1. "The accepted single-switch design leaves the bus enabled from the on-rail check until the
   switch is opened" (M3_R10 Firmware), or until LANDED (rule 6).

So the bus is live from a few seconds after J400 closes, with a person still at the rail, through the pad wait and the
flight. Step 3 raises PC1 only with the 1–2 Ω dummy in J121.

### Does the cold screen catch the bridge? (Calculation, PC1 and PE4 low)

| Cold state | CONT | BUS |
|---|---|---|
| Healthy match (Vf 0.3–0.2 V) | 96.2–99.4 mV | 96.1–99.3 mV |
| Open match | 141.5–146.2 mV | 0 |
| PYRO1_OUT bridged to 3V3 (or 3V3A) | 3.3 / 11.2 = 0.295 V (≈ 0.294 V for 3V3A) | 0.295 V with an intact match, 0 with an open one |

- The bridged reading is 2.96 × healthy and 2.0 × open.
- Meanwhile the match carries ≤ 0.29 mA: 3.3 V into the 11.2 kΩ bus divider, with the body diodes of Q120 and Q121
  back to back.
- Any bridge low enough in resistance to fire (under about 10 Ω) reads this way.
- The mandated CONT-upper / BUS bands therefore refuse it before PC1 (F8; M3_R10 "any ground fault is a hard refusal
  before PC1"; R19-SAF-04).
- **A bridge present at power-up cannot fire.**

### A bridge that forms after PC1 is high

The cold screen has already run, so it does not see this bridge.

- **If the 3V3 rail were held at 3.3 V,** the match would carry (7.4–8.4 − 3.3) V over a 2.8–4.5 Ω loop: about
  0.9–1.8 A, against the J-Tek's 0.75 A all-fire.
- **The AP63203 cannot hold it.** It does not sink current in PFM (Diodes DS41326 Rev 3-2, "Pulse Frequency
  Modulation"), so the rail is driven past U1's 4.0 V absolute maximum. That is the I-5 mechanism.
- **3V3A** carries about 0.6–1.0 A through R164 until that 0603 resistor (0.8–2.3 W) opens. Then VDDA, U4 and U5 are
  over-driven.

So it can fire, on the pad or in flight.

### Severity: Minor (doc)

1. **The cold screen reliably refuses first** for the defect a 0.51 mm pad pair can realistically carry from assembly:
   a bridge present at power-up.
2. **The later-fault case belongs to a class the records already disclose.**
   - **Where it is disclosed:**
     - §1 line 2340's own first sentence: "An OUT-to-GND bridge or a failed-short Q124 can fire an enabled match;
       coating and a prior cold screen do not prevent a later fault".
     - Owner row 1: "Q124 and the firmware that drives it alone keep the e-match from firing", with row 18 as the
       lever on the pad.
     - FMEA I-5.
   - **Its disclosed members are more likely than these two pairs:**
     - OUT–GND at 0.177 / 0.180 mm;
     - Q124 gate–drain at 0.520 mm (a round 25 triage observation);
     - C128 at 991 microstrain;
     - In2 3V3 at 0.300 mm from RAW_PROTECTED, over 132 mm.
   - **Mitigation and fault model:**
     - R173, D120, R164 and their copper are in the mandatory coat selection (ORDERING 8.3).
     - The R10 fault model is single-string: FMEA line 58, F8, and the owner decision of 2026-10-28.
3. **The board itself is not at fault.** It violates no AGENTS §2 rule and no stated requirement. What is wrong is that
   the record denies two members of a disclosed class.
4. **Grading this record error Critical would grade every disclosed member Critical too.** The brief excludes those as
   disclosed owner deviations.

### Fix options

1. **Text (recommended; no board change).**
   - Rewrite line 2340 and owner row 2.
   - Add the PYRO1_OUT bridges to GND, 3V3 and 3V3A to owner row 1 and to FMEA I-5. The exact wording is in the JSON.
   - No new refusal rule is needed. The existing bands refuse a pre-existing bridge at about 3 × the healthy reading.
2. **Board (an owner respin item).**
   - Hold PYRO1_OUT at least 1 mm from 3V3 and 3V3A: move D120 about 0.55 mm west, and move R164 about 0.45 mm north
     or re-draw the diagonal.
   - This closes two members of the class, but the closer OUT–GND members remain. It also restarts the clean-round
     count.
   - A GND guard is not a fix at PYRO1_OUT, because GND is foreign there (S-8).
   - H-9's 3V3 clamp does not close these routes either: a clamped rail lets about 1 A through the match.
     (Erratum, R27-TRI-05: the 3V3 clamp is not FMEA H-9; §4.2's H-9 is the load-switch gate-source capacitor, C120 on R10.)
3. **Procedure.** Owner row 18 (PC1 low until launch detection) covers both pairs on the pad. Nothing but spacing covers
   them in flight, as for OUT–GND and C128.

## Items the root flagged

### R26-ROUTING-03 (R26-TRI-09)

**Which plated pins change layer.** I checked every plated pad for same-net tracks on two copper layers:

| Pin | Net | Nearest GND via | Status |
|---|---|---|---|
| J440.3 | AUX_TX_WIRE | 3.900 mm | fails |
| J440.4 | AUX_RX_WIRE | 4.037 mm | fails |
| J400.2 | BAT_SW_RETURN | 3.027 mm | exempt (AUD-2 slow list) |
| J1.1 | BAT_IN | 6.512 mm | power net |

J121, J122, J410, J420, J9, J3 and J2 each carry one copper layer.

**The gate misses it.** route_check `--profile r10`, run on a copy, gives 0 failing and no AUX instance. Its loop
iterates PCB_VIA items only (route_check.py lines 2231–2250). The layer change came with D-R20-09, a generator change.

**Classification.** AGENTS §3 lists no port UARTs for R10. But D-R19-15 keeps them under the 1.5 mm partner rule
("the frozen board meets them", true only before D-R20-09). The R10 gate classes them as critical, and M2 says the gate
fails "a critical-signal-net layer change". The board breaks that recorded rule.

**A legal GND via fits within 1.5 mm.** Checked for a 0.5 / 0.3 mm via at (7.4,16.5) and (7.4,20.0), each 1.500 mm
from its pin:
- 0.300 mm to the pin's pad on all four layers;
- 0.60 mm inner-layer hole clearance against the DRU's 0.55 mm;
- 0.70 mm hole to hole;
- no other foreign copper within 1 mm on F.Cu or B.Cu;
- on In2 the via sits in the 3V3 fill, which the refill clears;
- M-6, S-8 and the D440 / D441 clamps (2.9 mm or more away) are unaffected.

**Fix (changes the board).**
- Add the two vias, then re-run DRC, K-plane, K-copper and route_check.
- Extend critical_via_no_gnd to plated pads.
- The non-board alternative needs a new decision moving the two nets to AUD-2's slow list, with owner acceptance. An
  allowlist entry would fail route_check's spot search, because legal spots exist.

### R26-POWER-02 (R26-TRI-02)

**Where 5.73 V appears as the four-stall corner or the bench voltage:**
- AGENTS §1, line 13;
- STATUS lines 11, 16 and 19;
- REQUIREMENTS F4 (line 58), F6 (line 60) and line 106;
- M3_R10 lines 270 and 590–591;
- ORDERING line 617 ("U9 stays on … at 5.73 V" and "run this test at 5.73 V");
- the handoff, lines 68–69;
- R10_VALIDATION row 21 and §4's C87 row;
- parts_qualification line 20;
- `r10_sch_check.py` line 295, generated into binding note line 589 and pinned by `test_r10_check.py` lines 399–402;
- D-R24-19 and D-R25-01, through a new D-R26 annotation.

Dated history stays as recorded.

**Replacement figures:**
- four-stall point 5.71 V (5.713 V);
- single drop-out 8.07 ms;
- window limit 7.50 ms;
- 7 ms-line margin 0.50 ms;
- fast-chatter fraction 19.7 % (19.6 / 14.8 / 4.5 % at 0.1 / 4 / 8 ms).

The bench condition becomes "U9 stays on for the whole run at 5.71 V". The 7 ms line itself holds down to 5.6465 V.

### R26-POWER-01 (R26-TRI-03): correct wording

"The worst admissible train is one open block per 100 ms placed late in the window (exchange argument:
C∘O − O∘C = (1 − a)(1 − b)(vc − vo) > 0). At the corner it trips U9 at 7.50 ms at 5.71 V (7.63 ms at 5.73 V). At the
7 ms pass line it holds EN at 1.1295 V at 5.71 V (1.1330 V at 5.73 V), against 1.116 V (Calculation)."

### R26-SAFETY-03 (R26-TRI-04)

The PA6 window does not change. With 1 % R60 / R61 its top edge is 5.27 V. The corrected shorted-match corner, after
U9 (≤ 45 mΩ) and U11 (≤ 85 mΩ), gives VLOGIC of about 5.34–5.47 V, so the window stays below it. The old 5.37 V figure
was the pessimistic one.

### Gate observation 2

Not a real error: no stated rule binds the text to `parts_budget.json`.
- It is the cause of the stale-figure class, and one such figure is stale now: the 5.73 V point (R26-TRI-02).
- The other budget-derived figures I checked are current: hold-up, post-trip hold-up, the F7 currents, the U9 bound,
  OVLO and the buck peaks.

### Parts observation 2

Not a real error.
- **The datasheet does not ask for it.** DS41326 §10 ties L1's saturation rating to the operating peak (Eq. 8) and asks
  for a DC rating of at least 1.35 × the load. It does not require Isat above the 2.5–3.1 A high-side limit.
- **L1 has large margin in operation.** The 3V3 operating peak is about 0.6–0.85 A, against 2.90 A.
- **The records make no claim.** No record claims a fault-current rating for L1.

## Observations (not counted)

Most are reproductions. The ones I re-examined are listed below, with the reason each stays an observation:

| Observation | Why it is not a real error |
|---|---|
| Safety 3 (TCR) | The limit falls to 7.18 ms at 70 °C, still above 7 ms |
| Safety 5 (TP81 timing) | The rail method meets 1 s. The TP81 alternative needs access the rail does not give, rests on an Inference and errs fail-safe |
| Safety 14 / 15 | Disclosed row 2 class |
| Power 5 (5.5 V) | A sensitivity point, and the scenario needs more conditions than the fault model allows |
| Power 6 / MCU 2 (PA6 lower edge) | Disclosed, and listed by round 25 |
| Routing 8 (D8 via) | An M2 review item for the final report |
| Routing 9 (row 30) | The figures are labelled with their board |
| MCU 4 (0.83 V) | 0.833 V at +1 %, within the stated bound to two figures |
| Docs_binding 1 | The R19-RTE-04 list is labelled history |

Details are in the JSON.

## Checks executed

- SHA-256 of the board before, during and after.
- pcbnew dump of 216 footprints, 1057 tracks and 307 vias; PYRO1_OUT adjacency; pin layer check; via-spot legality; C84
  and J3 geometry; under-body via scan; capacitor-distance scan.
- route_check r10 on a copy.
- Independent EN model, train, fraction and fire-budget re-solves, and git history of `loaded_pack_V`.
- pdftotext of TI SLVSEA3F, TI SLVSFC9C and Diodes DS41326.
- git grep of every quoted figure.

## Coverage limits

- No DRC run on a seeded board with the two J440 vias. Legality was measured against the DRU and design rules.
- The 3V3 rail's absorption at over-voltage, and its parts' breakdown, are Inference.
- No bench or firmware evidence.
