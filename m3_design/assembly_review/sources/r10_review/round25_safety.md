# Round 25 safety lens (Claude)

- Target: commit `c4bb56b`, PCB `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f`.
- The SHA-256 was the same before and after the review and matches `git show c4bb56b:` of the board. No tracked file
  changed.
- Rule: only real errors count. Full detail is in `round25_safety.json`. Probe scripts and outputs are in
  `.supervisor/r25_safety/`.

**Totals: 0 Critical / 0 Major / 3 Minor.**

- No AGENTS section 2 rule is violated on the built board. S-1 to S-9, K-actuators, K-ports and the full check_r10
  contract pass on a probe copy, and route_check finds 0 failing.
- No undisclosed single fault energises the bus, fires the match, or turns the board on with J400 open.
- All three findings are record or calculation errors.

## Findings

| ID | Kind | Sev. | What is wrong | Key number |
|---|---|---|---|---|
| R25-SAFETY-01 | doc | Minor | FMEA H-6 (line 36) still says to repeat the bench supply ramp after a suspected discharge with "turn-off 4.5–4.8 V, turn-on 4.9–5.2 V". R24-TRI-03 / D-R24-19 corrected ORDERING 8.3, REQUIREMENTS F9, M3_R10 and the sheet note to 4.29–4.80 / 4.72–5.25 V, but not the FMEA, although R24-SAFETY-03 had named it. STATUS line 16 therefore says wrongly that "every record" carries the corrected window. | Healthy boards turn off at 4.288–4.802 V (nominal 4.505 V, on the FMEA window's edge) and turn on at 4.723–5.251 V |
| R25-SAFETY-02 | calc | Minor | The hold-up after the PA6 trip, "0.157–0.182 ms with all ports on and 0.44–0.48 ms with the camera off / shed", is computed from 5.3 V. The same records define the trip window as VLOGIC about 4.8–5.2 V (PA6 0.44–0.47 V × 11 = 4.84–5.17 V), and M3_R10 Power even says "the trip at about 5.3 V". The figures appear in M3_R10 rule 8 and Power, REQUIREMENTS F6, ORDERING 8.3, owner rows 5 and 25, and binding-note obligation 43. | From the window: 0.103–0.164 ms (all ports on) and 0.291–0.430 ms (shed); 22–31 % of the break figure, not "about a third" |
| R25-SAFETY-03 | doc | Minor | The FMEA row I-11 / V-19 / H-6 (R10) (line 86) still starts "Current R10 (`1407e850…`; …)". f2b8251 bound it to the then-current board; c4bb56b did not update it. | The board is `92c3ad59…` |

Fixes (text only; no board change):

- **01:** in FMEA H-6, write "turn-off 4.29–4.80 V, turn-on 4.72–5.25 V, nominal 4.51 / 4.96 V (ORDERING 8.3,
  D-R24-19)".
- **02:** quote the post-trip hold-up over the stated window (0.10–0.16 / 0.29–0.43 ms from VLOGIC 4.84–5.17 V at
  300.8 µF). Strike "the trip at about 5.3 V". Write "a fifth to a third" in owner rows 5 and 25. Update the rule-8
  string in `m3_design/r10_sch_check.py` and regenerate the binding note.
- **03:** write "Current R10 (`92c3ad59…`; …)".

## Fix verification

| Decision | Measurement | Verdict |
|---|---|---|
| D-R24-18 BAT_FAULT_N chamfer | Via (17.1,82.8) to BAT_FAULT_N on F.Cu: 0.2000 mm at the legs and 0.2015 mm at the chamfer, (16.55,83.03)–(16.87,83.35), which is 0.4525 mm long. The diff from `1407e850…` is exactly the three BAT_FAULT_N pieces; F.Cu GND fill changes by −0.022 mm². No other safety-net gap changed. route_check finds 0 failing. | confirmed |
| D-R24-19 EN text | The corner model reproduces every figure: 10.345 / 20.111 / 26.023 ms; 8.204 ms at 5.73 V; 6.300 ms at 5.5 V; 5.956 V; 30.3–130.3 ms; ramp 4.288–4.802 / 4.723–5.251 V; chatter trip 20.0 / 24.4 %; PA6 edge 4.84 V above 4.802 V. The sheet note and binding-note rules 4, 5 and 8 and obligation 17 match. No single via open is left at Q120's gate, U1.28 or R91.1. Per-flight steps 2, 3 and 5 are consistent with the timing. | partly: FMEA H-6 was not carried (01); rule 8's hold-up basis (02) dates from round 23 |
| D-R24-02 (re-check) | No single via open splits ACT_GATE. S-8 is 1.050 mm at all four barrels. Gaps are 0.3609, 0.3413 and 0.4207 mm. | confirmed |
| D-R24-11 (re-check) | BAT_SW_RETURN is {J400.2, R165.1, D402.1}, with D402.2 on GND. The tap is 4.114 mm and the GND via 0.700 mm away. Only GND copper is within 0.6 mm. Infineon Rev 1.3 Table 3 gives IR ≤ 50 nA at 15 V, 25 °C. | confirmed |
| D-R24-22 | The check_actuators r10 messages use J400.1 / J400.2. | confirmed |

## Checks executed

- Board SHA-256 before and after the review.
- pcbnew outer-layer adjacency of 21 pyro / arming / switch / pack-live nets within 0.6 mm, exact to 1 nm, on
  `5516eeec…`, `1407e850…` and `92c3ad59…`, with a diff between them.
- Nearest-copper probes at the EN, gate and residual vias.
- A board diff from `1407e850…` to `92c3ad59…`.
- Single-open connectivity on ACT_GATE, ACT_FET_S, BAT_ENABLE, BAT_SW_RETURN, PYRO1_GATE, PYRO1_GATE_N, ACT_EN,
  LOGIC_SOURCE_ST and VLOGIC.
- Independent S-8 barrel and ring measurements.
- Topology dumps of every gate network and the switch chain.
- route_check, fit_check and the full check_r10 contract (37 rules) on a probe copy: all OK.
- The EN corner model and the post-trip hold-up model.
- Datasheet tables: TI SLVSFC9C pp. 7 and 9; Infineon ESD103 Rev 1.3 Table 3; AONR21357 and AON7524.
- Greps of the records for superseded figures.
- The round 24 safety report was read only after these findings were drafted.

## Observations (not counted): 11

Selected:

- **Q124 gate–drain pad gap (0.520 mm, F.Cu, recorded).** With the bus enabled, a bridge there fires the match (about
  1.3–1.4 A; Inference). This belongs to the disclosed failed-short-Q124 class, and the cold screen refuses a bridge
  that is already present.
- **U9 bypass paths.** U9.5–U9.6 are 0.200 mm apart. J1.1's In2 ring and the BAT_IN via (17.5,87.15) are 0.251 mm
  from In2 RAW_PROTECTED. Each puts the board on with J400 open. Step 2 catches it, but its list of causes omits these
  paths.
- **Sense-plausibility rule (R22-POWER-02).** It calls a persisting PA6 trip a sense fault. A real low pack between
  U9's turn-off and the trip does the same. The rule's action is harmless in both cases.
- **Labelled history.** The S-8 table row "J400.2 In1 GND 0.250 since D-R20-05" is labelled history; the board now has
  0.550 mm.

## Coverage limits

- This lens ran no DRC or kicad-cli; the DRC results come from the records.
- Inner layers were checked only at the protected barrels and at the BAT_IN / BAT_SW_SOURCE barrels.
- No hot-plug or transient simulation was run.
- The makers give no leakage figures at temperature.
- No firmware or physical test exists.
