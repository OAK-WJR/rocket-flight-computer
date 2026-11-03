# Requirements-audit implementation preflight

2026-10-28. Read-only research and candidate routing plans, before AUD/GAP source changes. The owner-answer
board is `b860afbe406d7daec9757ccde89987d3439b32e0b1f8078bb01363be1704baa1`; two fresh full builds agree
byte for byte and the regenerated package/full gate pass. Git staging and committing are blocked by the
environment's denial of the worktree `index.lock` write. No new full review round or audit implementation is claimed.

## Part choices for the audit pass

| Item | Selection and evidence |
|---|---|
| AUD-1, C92 | Reuse Samsung CL10A475KO8NNNC / C19666, 4.7 µF 16 V ±10% X5R 0603, already used at C23/C28. At a conservative 4 V, the maker's typical bias curve retains 0.611246 of nominal; 4.7 × 0.9 × 0.85 × 0.611246 = 2.198 µF versus TPS709's 1.5 µF minimum effective output capacitance. Inferred qualification using typical curves, not a guaranteed production minimum. Samsung marks it NRND. |
| AUD-3, Q120/Q121 | Retain AON6403. Stocked AOS AONR21357 / C431196 is a smaller candidate, with ±25 V gates and 12.3 mΩ maximum at −4.5 V. Its hot resistance at minimum drive relies on a typical curve; the guaranteed 125 °C row uses −10 V. Existing R120 100 kΩ, R121 10 kΩ and C120 2.2 µF imply a 20 ms nominal gate time constant, approximately 25.81 ms at the stated upper allowances. A shorted igniter/active Q124 exposes the pair to up to 8.909 W during linear transition. SOA curves assume a reference heatsink or 1 in² 2 oz board. No replacement was qualified in this bounded search; this is not a claim that no smaller suitable part exists. |
| AUD-7, R412/R422/R432 | Reuse UNI-ROYAL 0402WGF1002TCE / C25744, 10 kΩ 1%, 0402, 62.5 mW; 3.3²/9800 = 1.111 mW. |
| AUD-7, R150–R153 | Reuse UNI-ROYAL 0603WAF1001T5E / C21190, 1 kΩ 1%, 0603, 100 mW through 70 °C. Conservative chafe-fault dissipation: 8.4²/980 = 72 mW. Preserve the electrical resistance and clamp. |

Sources: [Samsung exact capacitor and curves](https://product.samsungsem.com/mlcc/CL10A475KO8NNN.do),
[TI TPS709 pp. 14–15](https://www.ti.com/lit/ds/symlink/tps709.pdf),
[AOS AONR21357 pp. 1–5](https://www.aosmd.com/res/datasheets/AONR21357.pdf),
[UNI-ROYAL maker specification pp. 2, 4–5](https://datasheet.lcsc.com/datasheet/pdf/0a975aaa49b7c97f38a963127be4a823.pdf).

Fresh public JLC API checks, 2026-10-28 18:41–18:43 UTC: C19666 3,101,844; C25744 17,663,300;
C21190 32,883,561 (all Basic); C431196 56,301 (Extended). These are research snapshots, not an order-day
stock qualification or a quote. The full revised BOM still needs pricing and stock checks after regeneration.

## Generator ownership and removals

The active build families are core, usb, pyro, power, signals and ground. The separate ports/servo/status modules
are historical/inactive in the normal build. Implement through generators only.

- Circuit slice: `circuit.json`, `pin_table.tsv`, `masses.json`, `r10_sch.py`, `r10_sch_check.py`, `r10_parts.py`,
  and R10-only `check_actuators.py` changes. Keep archived R9 behavior.
- Layout slice: `r10_place.tsv`, `r10_route.py`, active route modules, `r10_fanout.tsv`, and `r10_post.py`.
- Gates: `check_r10.py`, `route_check.py`, corresponding tests, narrow thermal-pad exception and return-path scope.
- Records: REQUIREMENTS, AGENTS, STATUS, ORDERING, M3_R10, FMEA and parts qualification. Cite AUD entries for
  every narrowed gate. Rebuild canonical schematics/PCB, budgets and binding note; refresh fabrication evidence.

Remove J123/R160/R161/C160/D122 and make PC13 NC (AUD-4); remove TP84/85/86/87/89/92 (AUD-5).
Keep TP74/TP88 and the specifically retained hot-plug/pyro contacts. Remove GPS/radio IO LDO cells (AUD-8),
tie U411/U421 pin 7 to main 3V3, retain OE-low sequencing, series resistors and ESD. TI TXU0202 §12.1 recommends
0.1 µF near supply pins and §12.2 shows separate bypasses. Check the shared C440/C450 route to both pins 3/7;
if it cannot be short, retain existing C443/C453 as direct 3V3 bypasses with a documented AUD-8 refinement.
Do not silently delete required local decoupling. [TI TXU0202](https://www.ti.com/lit/ds/symlink/txu0202.pdf).

AUD-2 changes the return-path geometry scope, not ARM topology or all routing hygiene: omit named filtered
ADC, ACT_EN/DRV/GATE and port EN/FAULT/OE nets from 1.5 mm partner-via and one-In2-region checks. Preserve
fast-interface checks, PYRO1_GATE/OUT/BUS partners and S-8. AUD-10 makes harmless graph artifacts and the
6 mm legend-distance rule review findings; missing/incorrect legends, electrical continuity, DRC and fast returns
remain blocking. Add J410/J420 pin tables if a legal location exists. AUD-6 adds 0.5 mm to the routing primitives
and narrows only the fire-only runs; keep the continuous BAT_IN/U9 feed and existing ACT_FET_S bridge.

## Candidate layout changes requiring DRC

Coordinates below were planned from the unchanged placement/track geometry. Courtyard and individual route
checks are preflight only; none substitutes for the integrated fill, DRC, parity or board gates.

- GAP-2: keep U9 and the hot-plug-qualified BAT_IN feed fixed. Move C82 to B (39.8, 74.75), rotation 90°;
  D9 to B (43.35, 73.45), rotation 90°; R92 to C82's vacated F site (33.9, 65.775), rotation 90°.
  The three candidate courtyards have no collisions in the preflight. C82's RAW pad at (39.8, 76.25) is 3.39 mm
  from the U9 OUT-pad centre. Candidate OUT via bank: (40.2, 77.2), (40.9, 77.2), (41.6, 77.2), (42.3, 77.2).
  Candidate GND vias: C82 (39.8, 72.15), D9 (43.35, 69.8). Reuse the old C82 RAW/GND vias for R92 and remove
  R92's old fanout. The old OUT bank conflicts with relocated C82's paste.
- GAP-3: U401 EP is x 27.0–28.2, y 12.6–14.6. The maker's diamond is (27.6, 12.85), (27.6, 14.35),
  (27.25, 13.6), (27.95, 13.6). Use 0.5 mm rings/0.3 mm drills to retain the project drill floor; maker drill is
  0.2 mm. Narrow the no-via-in-pad exception to these GND holes inside U401.11, preserve all other pad checks,
  and specify filled/capped treatment to prevent solder wicking. Confirm this with the assembly quote.
  Existing GPS_FAULT_N crosses the proposed diamond. Candidate F route: (26.9, 15.825) → (28.5, 15.825) →
  (29.1, 15.225) → (29.1, 11.65) → (31.6, 11.65). Move its end via from y 11.425 to 11.65 and extend the B
  vertical. This candidate cleared baseline F copper and the four via rings at 0.15 mm in the preflight.
- C92 cannot simply shrink in place: B status lanes y 47.0/47.9 pass between its existing 1210 pads.
  Candidate smaller-cap location: B (34.2, 45.2), rotation −90°; new IO/GND routes need checking.
- Keep centres/rotations of the resized FAULT pull-ups and servo resistors; redraw their pad entries to the new
  actual pad centres, including R422.1's hard assertion. Retag the former GPS/radio B-supply vias at
  (35.5, 17.8)/(35.5, 29.8) to 3V3 and investigate connections to In2 3V3 near (33.8, 18.7)/(33.8, 30.7).
- Remove pullpin routing, TP87's branch, TP85's intermediate anchor, the R84→TP89 branch/via and TP84's
  excursion. USB inherited pad assertions/branches for TP86/TP92 must disappear while preserving R110's sense
  connection. Do not leave a reference to deleted U422.1 in the radio power route.
- Remove slow-only GND partners at (25.2, 55.0), (28.2, 59.6), (27.2, 65.4), (16.2, 71.2), (9.9, 70.4),
  (33.1, 35.825), and control-only PORT_CONTROL_GND entries. Check (25.7, 30.6) separately: it also stitches
  a pour island. Keep (33.2, 43.85)/(33.15, 40.55), which serve CAM_MCU_RX. Remove CH1's slow-sense plane arms
  and the Q121-gate bay, while preserving barrel clearance, the R13 notch and D120's 3V3 corridor. Recheck S-8.

## GAP calculations and firmware contract to implement

GAP-1: compute simultaneous pack loading, using I_fire = (Voc − Rpack × I_other)/(Rpack + R_fire).
Use a conservative provisional R_fire excluding the pack of 4.44 Ω: R134 2.04, e-match 2.0, harness/fuse 0.30,
and board copper plus hot FETs 0.10 Ω. Remeasure the final board to justify the 0.10 Ω allowance. Also solve
V = Voc − Rpack × (V/R_fire + I_servos + P_other/V) with the existing maximum full-port/logic power budget,
Rpack 0.15 Ω, and 0–4 × 1.92 A servo stalls at Voc 6.0/7.4/8.4 V. Label power/stall envelopes as inferences.
The proposed R10 compatibility constraint is an e-match all-fire ≤0.8 A within 20 ms (1.5× target 1.2 A) for
the four-stall/full-port 7.4 V case. Keep R134 unchanged. Explicitly retain pack-at-fire and actual e-match/harness
qualification before flight; voltage/sense readings never veto an in-flight fire. This is not a physical test.

GAP-3: current worst LDO loss is 0.40618 W. At the specified 70 °C bay ambient, assumed 80–110 °C/W gives
102.49–114.68 °C junction, below 125 °C. The required measured effective resistance is ≤135.41 °C/W. Thermal
vias do not establish that resistance by themselves. Retain full-load thermal qualification and label the estimate
Inference. [TI TPS7A91 §7.1.4, §7.4.1 and DSK drawing pp. 23, 25, 35](https://www.ti.com/lit/ds/symlink/tps7a91.pdf).

GAP-4: remove the OS-CON reflow qualification from C84's active R10 order remarks. Select post-reflow hand fitting
of C84 with an assembler-qualified process unless the actual MA capacitor obtains a maker reflow qualification;
do not invent a solder-temperature rating.

GAP-5: proposed IWDG prescaler 4, RLR 127 gives 15.238–17.415 ms at 29.4–33.6 kHz. Require completed 100 Hz
safety passes plus scheduling jitter below 15.238 ms; feed only after a complete pass. Enforce junction ≤105 °C
for all silicon revisions, throttling before that ceiling. Floating-MCU gate discharge: R = 10 kΩ || (220 Ω + 1 kΩ),
220 nF with +10% tolerance/+15% temperature and R +2% gives τ ≈0.3086 ms; 3.6→0.4 V takes 0.678 ms.
Allocate ≤0.7 ms gate release and ≤1 ms reset/synchronization latency: total 19.115 ms, below the 20 ms fault
contract. Keep independent timer/DMA termination for normal ≤20 ms pulses. These are implementation/bench
obligations, not existing firmware or measured off-state guarantees.
[ST DS12110 Rev 11 Tables 39/136 pp. 129/233](https://www.st.com/resource/en/datasheet/stm32h743zi.pdf).
Bourns' ≥1 Ω single-pulse curve gives 90 W at 10 ms and 27 W at 100 ms; logarithmic interpolation gives
approximately 62.64 W at 20 ms versus a 35.64 W/0.713 J shorted-igniter pulse. The chart's temperature/test-board
conditions are not explicit; hot pulse durability still needs qualification.
[Bourns CRM pp. 1–3](https://www.bourns.com/docs/product-datasheets/crm.pdf).
