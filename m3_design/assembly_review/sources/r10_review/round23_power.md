# Round 23 power review (Claude)

Target commit `c70d261`. PCB SHA-256 `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1` before and after.
**Result: 0 Critical / 0 Major / 4 Minor (all new).** Evidence: [round23_power.json](round23_power.json); probe scripts and
outputs in `.supervisor/r23_power/`.

Angle (different from round 22): transients and behaviour over time, not DC budgets. Labels: Calculation, Inference
(not stated by the maker or not measured). Board facts were read with the pcbnew API, not taken from the records.

## Findings

**R23-POWER-01 (Minor): the hold-up left after the PA6 trip is about a third of the quoted ride-through, and no record states the narrow window the trip voltage must sit in.**
- The quoted 0.464–0.539 ms (all ports, SD writing) and 1.304–1.412 ms (camera off, logic shed) at 300.8 µF run from the
  break at 7.4 V to 3.8 V (`parts_budget.json`). REQUIREMENTS F6 defines the need as the time *after the PA6 watchdog fires*.
- The trip must sit above U9's turn-off corner and below the lowest legitimate VLOGIC (Calculation):
  - Above U9's corner (BAT_IN 4.29–4.78 V; SLVSFC9C p9, 1 % divider, ±0.1 µA leakage). Otherwise, in a slow sag, U9
    cuts the board before the shed starts.
  - Below the four-stall-plus-fire corner (BAT_IN 5.37–5.54 V; 7.4 V EMF, 0.15 Ω). Otherwise the shed fires at deployment.
  - So the window is VLOGIC about 4.8–5.2 V.
- Hold-up from a 5.3 V trip at 300.8 µF (Calculation):
  - 0.157–0.182 ms with all ports on, 0.44–0.48 ms with the camera off and logic shed: 34 % of the quoted energy.
  - "100–220 µF would do" for about 0.2 ms does not hold: from 5.3 V that is 0.05–0.13 ms with the ports on.
- Fix (text only):
  - state the trip window;
  - quote hold-up from the trip voltage;
  - correct the R19-REQ-07 owner row and F6.

**R23-POWER-02 (Minor): the J400 chatter acceptance (longest drop-out < 10 ms) does not screen a chatter train.**
- Averaged over a train with open fraction d, EN settles at ((1−d)·Vb/R_top − I_lk) / ((1−d)/R_top + 1/R81). This does not
  depend on C87.
- U9 turns off once d exceeds the following, however short each drop-out is (Calculation):

  | Pack | Worst case | Nominal |
  |---|---|---|
  | 5.73 V | 21 % | 26 % |
  | 6.0 V | 25 % | 30 % |
  | 7.4 V | 42 % | 46 % |
- Example: 100 Hz with 3 ms drop-outs (30 % open) at 5.73 V trips U9 in 32–92 ms.
- The single-drop-out figures reproduce exactly: 10.65 / 20.47 / 26.41 ms at 6.0 / 7.4 / 8.4 V, 8.50 ms at 5.73 V, and
  5.917 V needed for 10 ms.
- Result: a flight reset from a chattering switch that passes the stated test.
- Fix (text only): in REQUIREMENTS F6 and ORDERING 8.3, also require that U9 stays on at 5.73–6.0 V under flight
  vibration, and an open fraction below 20 % in any 100 ms window.

**R23-POWER-03 (Minor, about the analysis, not the board): `round22_alternates.md` §1.3 gets the TPS259470A persistent-short case partly wrong.**
- **Confirmed:** the retry mechanism. U9 cools by 10 °C after TSD at 154 °C, then waits tRST 110 ms (SLVSFC9C p10–11, p37–38).
- **Current.** In a hard short VOUT < VFB 1.9 V, so the current is foldback-limited below ILIM (p32 note 2; TI gives no value,
  Inference). It is not "about 4.4 A". That figure applies only above 1.9 V.
- **Logic.** RAW_PROTECTED never reaches U11's 2.5–2.8 V UVLO or the AP63203's 3.3–3.7 V UVLO. So the MCU does **not**
  reboot every cycle, and FLT is unobservable (R89 pulls up to a dead 3V3). Reboot attempts are possible only for a
  resistive overload of about 0.8–2 Ω at 7.4 V.
- **C84.** It sees no inrush in a hard short (U11's reverse blocking), and about 0.1 A in the overload band.
- **Not stated by the analysis.** U9's junction reaches 154 °C (above the 125 °C operating maximum, p8) on every cycle for
  as long as J400 stays closed. The average dissipation is about 0.1–1.5 W, depending on the unspecified foldback current
  (Inference).
- No AGENTS §2 property changes.
- Fix (text only): correct §1.3 and the ORDERING 8.1 option text.

**R23-POWER-04 (Minor): BAT_FAULT_N (PA5, EXTI5) also pulses low whenever U9 blocks reverse current.**
- SLVSFC9C Table 7-3 p38: reverse current → FLT L, not latched. RCB trips at −22…−36 mV and releases at 83–125 mV
  (p10–11).
- Any BAT_IN drop faster than RAW_PROTECTED's own load slope (about 15–30 V/ms) asserts it (Calculation/Inference).
  Examples: contact bounce, servo-driver current edges on a stiff pack, hot-plug.
- The pin table and F10 call PA5 only "BAT fault".
- U11's ST during its own reverse blocking is not stated by TI (Inference), so PA4 may also glitch.
- Fix (text only): in `pin_table.tsv`, the binding-note obligations and M3_R10 Firmware, add the reverse-blocking meaning of
  PA5, a deglitch rule (no refusal or reset on one pulse; rate-limit EXTI5), and the PA4 deglitch. The PA5 edge could
  optionally start the shed early.

Round 22's power report (opened only after these were written) had R22-POWER-01 / -02 (single-via grounds and taps). It has
none of these four.

## Asked-for analyses (no further finding)

### Brown-out order as RAW falls (Calculation)

In a slow sag with J400 closed, the rails go in this order:
1. **PORT_5V3** leaves regulation first, at RAW about 5.77 V with the camera on (5.57 V with it off).
2. **PORT_4V8** follows at RAW about 5.31 / 5.10 V (TPS7A91 dropout ≤ 0.2 V, SBVS282A p5).
3. **U9** cuts the whole board at BAT_IN 4.29–4.78 V, while 3V3 is still regulated.
4. **During hold-up:**
   - the ports collapse (whether or not U11 blocks, IRCB 0.2–2 A);
   - then 3V3, below VLOGIC about 3.4 V and the AP63203 UVLO (2.86–3.26 V);
   - then the MCU at BOR (VBOR0 falling 1.58–1.68 V, VBOR1 1.95–2.06 V; DS12110 Rev 8 Table 126).

At four stalls (5.73 V) only the camera supply droops, by about 0.13 V.

**PC1 / PE4 stay defined throughout.**
- Above BOR they are driven.
- Below BOR the MCU is in reset and R123 2 kΩ, R127 1 kΩ and R128 10 kΩ / C126 hold them low.
- RAW_ACT can stay on 39–85 ms after Q122 drops out (C120 with R119 ∥ R120), by design; firing still needs PE4.

### Fire pulse and tail (Calculation)

- **Q124 tail:**
  - 0.05–0.10 ms after a commanded low;
  - 0.24–0.50 ms after a reset (PE4 Hi-Z);
  - both inside the 1.5 ms allocated in the 34.853 ms guard.
- **R134 with a shorted match:** 35.8 W, against about 46 W at 36 ms on the CRM2512 pulse curve (reading is Inference), a
  1.29× margin.
- **Four stalls plus a shorted match:** BAT_IN about 5.37 V, above U9's corner.
- **Fire-end overshoot:** about 0.08 V, far below OVLO (9.62 V minimum).

### USB plug and unplug, and port hot-plug

- **USB with the pack on.**
  - U11 is in VCOMP mode (PR1, CP2 and OV2 grounded) and stays on the pack. Plugging USB in only re-runs the settling timer.
  - A pack below USB switches over in 100 µs, with a dip of about 0.1 V.
- **USB from a legacy always-on source.** Ringing can reach 7.0–8.9 V before D4 clamps, against U10's 7 V absolute
  maximum (Inference). This is a bench item and is already in ORDERING §5's legacy-source check.
- **Port hot-plug.** A module with 10 / 47 / 100 µF of input capacitance dips the shared PORT_4V8 rail to 4.3 / 3.2 / 2.3 V
  for 0.05–0.5 ms (Inference). That can reset a module on another port; there is no flight effect. A one-line "wire port
  and camera leads with J400 open" rule in ORDERING 8.4 would close it (not filed).

### Single-via IC grounds (D-R22-02)

- **Re-measured.**
  - The U10.2 + R7.2 island is 2.89 mm² with one via, (9.00, 27.84).
  - U402.2's island is 5.70 mm² with one via, (32.30, 59.50).
  - R8.2's island is 6.96 mm² with one via, (9.95, 30.60).
  - `single_via_opens` reports 33 taps, 15 exceptions and 0 issues.
- **What an open does (Inference; SLVS841G is silent on an open GND).**
  - The IC's quiescent current can return only through its pin protection. Its ground therefore floats to about one diode
    above OUT.
  - IN − GND then nears the 2.35–2.45 V UVLO, so OUT limps at about 2–3 V or cycles. The result is loss of the camera
    supply (U402) or of bench USB (U10).
  - FAULT is an open drain to that floating ground, so CAM_FAULT_N / USB_FAULT_N cannot report it. CAM_5V_SENSE on PB1 can.
  - R85 / R430 return to board ground, so the current limit loses its reference. This matters only with a second fault.

## Fix verification

| Decision | Verdict | Measured |
|---|---|---|
| D-R22-01, -05, -06, -07 | confirmed (no copper change) | PCB hash identical at `ec8cb98` and `c70d261`; no `.kicad_pcb` / `.kicad_dru` / placement diff |
| D-R22-02 | confirmed | 33 taps / 15 exceptions / 0 issues; islands as recorded; reasons consistent (the FAULT-flag limit could be added) |
| D-R22-03 | confirmed | 0.496 / 0.888 / 1.809 V; only that text object changed |
| D-R22-04 | confirmed | EN 2.032 V nominal, 2.063 V with 1 % parts |
| D-R21-02 | confirmed | U2.1 has no single point |
| D-R21-05, D-R20-11, D-R19-10 | confirmed | Turn-on 30.3–128.6 ms; immunity 10.65 / 20.47 / 26.41 ms; 8.50 ms at 5.73 V; 5.917 V floor (see R23-POWER-02 for trains) |
| D-R19-04 | confirmed | Q122 network on the board; bus stays on 39–85 ms after Q122 drops out |

## Fix now (all text only, no board change)
- **R23-POWER-01:** state the PA6 trip window and the hold-up from the trip voltage; correct the "100–220 µF" sentence.
- **R23-POWER-02:** add the functional pass rule and the open-fraction limit to the chatter acceptance.
- **R23-POWER-03:** correct the hard-short paragraph of `round22_alternates.md`.
- **R23-POWER-04:** add the reverse-blocking meaning of PA5 and the PA5 / PA4 deglitch rules.

## Limits
- No SPICE and no measured waveforms.
- TPS25947 foldback and time-to-TSD are read from plots (Inference).
- Capacitor derating is the records'.
- TI is silent on the TPS2553 open-GND case and on TPS2121 ST during reverse blocking.
- Module input capacitances were not read.
