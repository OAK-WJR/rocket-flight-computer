# Round 20 power review (Claude)

Target commit `6628488cf34bf33bdf104cb4383fcbe447c5da65`. PCB SHA-256
`50a39de5b76dec3cb58bbb1b0ab528fd4d65098de9dfe8f89f49e2e7adcbd976`, the same before and after the review.
**Result: 0 Critical / 0 Major / 3 Minor (all new).** The structured evidence is in [round20_power.json](round20_power.json).

Scope: battery entry to every rail. That covers U9 / C87 / R166 / C88 / C84, VLOGIC, 3V3 / 3V3A, PORT_5V3 (U400 / L400, U402),
PORT_4V8 (U401) with the new AUX port, RAW_ACT and the R134 fire path. The review checks the D-R19 fixes that touch power,
IPC-2152 widths, via counts, thermal reliefs, hot-plug, brown-out and ride-through.

## Findings

**R20-PWR-01 (Minor): the AUX allowance's thermal basis looks at U401 alone.** The arithmetic is right: 0.4897 W gives
123.86 °C at 70 °C with 110 °C/W, and the 0.5 W floor gives 112.6 mA. But TI's RθJA (62.5 °C/W, SBVS282A p4) and the
inferred 80–110 °C/W cover the part's own heating only.

In the same allocation case, other parts heat the same In1 GND plane, which is U401's only heat path:
- U400 and L400, 8.7–13.3 mm away, lose 1.2–2.2 W (at the budget's own 80–88 % efficiency).
- Logic and SD writes lose another 1.4–2.2 W.

The board totals about 3–5 W. A 46 × 90 mm board in still bay air has about 10–15 °C/W to the air (Inference), so the
board itself runs tens of degrees above the 70 °C bay. Any part of that rise beyond 1.1 °C breaks the 125 °C floor.

U400 has no junction estimate at all. At 1.56 A it dissipates about 0.46 W, a rise of about 41 °C at 89 °C/W (DS41326 p4),
before neighbour heating. The consequence is loss of tracking and telemetry, not a pyro hazard. Real port draw is probably
well below the allocation.

Fix (no CAD change):
- State the limit as a total PORT_4V8 current (≤ 0.56 A, any split).
- Label the figure as self-heating only, or add a coupled term.
- Make the allowance conditional on a 70 °C power-knot measurement of U401, U400 and L400 at the allocation loads.

**R20-PWR-02 (Minor): the LDO's regulation tap rides on the first OUT via only.** R402.1, the 49.9 k FB top resistor at
F(30.575,12.6), joins PORT_4V8 only through via (29.75,12.6). On a copy with that via removed, DRC finds R402.1
unconnected. The power still flows through the new (29.75,9.95), so the regulator stays on but loses its feedback. R403
then pulls FB to GND, and PORT_4V8 rises to PORT_5V3 minus dropout: about 5.2–5.55 V on all three ports. That is above the
LR900's 4.5–5 V and the M100 Mini's 3.3–5 V. GPS_RX_MCU on F.Cu at y 11.0 blocks a quick F.Cu link to (30.5,9.95).

Fix:
- Now: add a 4.71–4.87 V PORT_4V8 check at J410.1, J420.1 and J440.1 to the first-article and pre-flight steps
  (ORDERING 8.3).
- At the next board change: give R402 an independent tap.

**R20-PWR-03 (Minor, documentation): two documents contradict the hold-up model.** M3_R10 lines 323–324 and
R10_VALIDATION line 1924 say the ports are off during hold-up because U11 blocks reverse current. The TPS2121 detects reverse
current only above IRCB 0.2 / 1 / 2 A (SLVSEA3F p8). The ports-on back-feed is about 1.6–2.2 A, inside that spread.
`parts_budget` therefore assumes, correctly, that C84 carries the ports, and the 0.464–0.539 ms figure depends on that.

Fix: reword both lines (exact text in the JSON).

## Round 19 fix verification

| Decision | Verdict | Measured |
|---|---|---|
| D-R19-09 C84 (VLOGIC) | confirmed | Removing either via leaves 0 unconnected; removing both isolates C84. 25.9 mΩ; current splits 0.56 / 0.44 A |
| D-R19-09 U402 IN | confirmed | Either via removed: 0 unconnected; both removed: U402.1 isolated |
| D-R19-09 U401 IN | confirmed | Either via removed: 0 unconnected. L400 → U401 6.08 mΩ |
| D-R19-09 U401 EN | confirmed | Either via removed: 0 unconnected; both removed: EN isolated |
| D-R19-09 U401 OUT | partly | Power path is doubled; the FB tap is still single (R20-PWR-02) |
| D-R19-14 J440 feed | confirmed | Two vias, either one sufficient. 29.92 mΩ, 9.0 mV at 0.3 A; 0.59 °C (IPC-2152) at 0.3 A |
| D-R19-14 AUX allowance | partly | Arithmetic reproduced; the thermal basis is incomplete (R20-PWR-01) |
| D-R19-14 ride-through | confirmed | 0.464 / 0.539 ms reproduced; the model is conservative |
| D-R19-10 C87 | confirmed | τ 50.0 ms; turn-on 87.6 / 55.5 / 44.6 ms; drop-out ride-through 19.2 / 32.7 / 41.2 ms. The worst case, 12 ms, is now only 1.2× the F6 10 ms criterion |
| D-R19-04 / -02 / -07 | confirmed | The fire-path copper is unchanged against a3144b15. The GND fire return Q124 → J1.2 solves at 0.69 mΩ over the window y 45–90. The via move is as recorded; C84 has no paste |

## Closed without a finding

- The single vias at U11.2 and on 3V3A are disclosed respin items. Seeded removal confirms each is a single via.
- J440.1 is 0.55 mm from In2 3V3, the same clearance as J9.1.
- The new VLOGIC vias sit 0.25 mm from inner copper, which is legal.
- LDO soft-start inrush is below 1 A against the 1.45 A foldback.
- IPC-2152 rises on the changed runs are at most 10.3 °C (U402 IN at 1.25 A).
- The hot-plug inputs are unchanged on BAT_IN.
- The L1 bridge via is confirmed.

## Executed

- Board SHA-256 checked before and after.
- kicad-cli 10.0.7 DRC on a copy: 0 violations, 0 unconnected.
- 24 seeded via-removal DRCs.
- A copper diff of the power nets against 1e60441.
- Six `tools/dc_solve.py` runs.
- A barrel-wall scan of every power-net hole.
- IPC-2152 fits.
- Recalculation against TI SBVS282A / SLVSEA3F / SLVSFC9C and Diodes DS41326.

Probe files are in `.supervisor/r20_power/`.

## Limits

- No thermal simulation or measurement.
- The hot-plug model was not rerun.
- DC solves assume room-temperature copper and 20 µm plating.
- Module input ranges come from the project records.
- The working tree after 6628488 was not reviewed.
