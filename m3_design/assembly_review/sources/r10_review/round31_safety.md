# R10 round 31: safety lens

Target commit `3366287`, board `a0ec075e…`. Board SHA-256 before and after:
`a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (unchanged). Brief: `.supervisor/r31_review_brief.md`,
lens queue `## safety`. Strict rule: only real errors count.

**Totals: 0 Critical / 0 Major / 0 Minor real errors.** 16 observations, not counted.

## Findings

None.

## What was checked

- **AGENTS §2 on the board as built.** The pyro bus is taken after the Q120 / Q121 load switch (BAT_IN → ACT_FET_S →
  RAW_ACT → R134 → J121.2). Q124 has R126 220 Ω series from U1.3, R128 10 kΩ gate to GND (its source), C126 220 nF gate
  to GND and R127 1 kΩ MCU-side pull-down. Q120 / Q121 have R121 10 kΩ series, R119 / R120 100 kΩ and C120 1 µF gate to
  source. Q122 has R122 1 kΩ, R123 2 kΩ and C123 10 nF. All default off in reset or unpowered.
- **§2.5 labels.** Swept the current safety figures in AGENTS §1, M3_R10 (CH1 pyro, retained deviations, firmware
  rules 1–13), R10_VALIDATION §1 and owner rows 1 / 2 / 5 / 7 / 24 / 25 / 33 / 36, FMEA H-6 / I-5 / I-2 / H-2 / I-7,
  ORDERING 8.3 and the handoff. Every figure that rests on an inferred input carries an Inference label. Those inputs
  are the BAT54 drop, driver resistances, plate model, board θ, fire-budget hot factors, gate-discharge criterion,
  hard-bridge pin behaviour, PC14 survival and EN leakage at temperature.
- **Firmware rules 3 and 4** in the binding note, M3_R10, ORDERING 8.3 and FMEA I-2 / H-2:
  - The four sources agree.
  - U3.3 is QSPI_IO2 and R127.1 is PYRO1_GATE_N. The 0.91 kΩ reading is 1 kΩ ∥ 10.22 kΩ.
  - τ is 47.8 / 53.0 / 58.3 µs, from 238.6 Ω × (C126 ±10 % + 2.25 nF).
  - R120.2 and C120.2 sit on Q120.4's own B.Cu island. So the |VGS| ≥ 4.5 V probe sees a Q120 gate that both of its
    vias have cut off.
  - BAT_IN − RAW_ACT > 0.2 V separates the body diode (0.7–1.0 V) from two FETs at ≤ 12.3 mΩ each.
- **§1 pair table and owner rows 1 / 2.** Every distance reproduces on `a0ec075e…` with pcbnew shape collide at 0.5 µm,
  for example:
  - OUT to GND 0.177 / 0.180 mm; R173.1 to Q124's source via 0.500 mm;
  - OUT to 3V3 / 3V3A ≥ 1.040 mm; the gate nets to 3V3 / 3V3A ≥ 1.0585 mm;
  - OUT to BUZZ_DRV 0.794 mm; CONT_MID to Q123.1 / R134.2 0.175 / 0.250 mm;
  - the EN-node and C87 / R81 pairs; S-8 at 1.021 / 1.050 mm on 12 barrels.

  Every consequence figure also reproduces:
  - cold bands 99.37 / 99.34 and 146.2 / 0 mV; the bridge readings 102.0 / 55.5 mV, 1.213 V, 1.377 V and 0.295 V;
  - 0.9–1.8 A, 0.6–1.0 A, 3.23 V and 47 µs;
  - the EN leak limits and harness EN voltages;
  - the ESD ramp window;
  - the Q122 and Q120 gate figures, including 4.74 V / 31.9 ms, which the budget computes at a 6.0 V pack.
- **Per-flight checks and first-article steps against the circuit.**
  - Step 2 (J400 open): the bank pulls J121.2 below 56 mV, even at Q121's 5 µA IDSS at 55 °C.
  - Step 3 (dummy load): CONT ≈ BUS, and with EN τ 66 ms the board is off well inside 1 s.
  - Step 4: the in-circuit parallel path is about 22 kΩ, which does not disturb the match reading.
  - Every probe coordinate and coating selection matches the board.
- **Single faults across the whole board.** Scanned every foreign item within 0.6 mm of the arming, gate, fire,
  sense, enable and buzzer nets on all four layers, and the In2 3V3 fill against every higher rail. Every route that
  could energise the bus, fire, or turn the board on with J400 open is either:
  - a disclosed class: I-5, row 2, row 24, the OUT-to-GND residuals, or a failed-short Q124; or
  - a class an earlier triage has already ruled not counted: the non-exhaustive I-5 lists, or the U9 bypass.

## Observations (not counted)

1. **More I-5 routes on In2, each 0.2508 mm from the opposite fill.** The VLOGIC vias (29.8,81.15), (34.5,62.4) and
   (34.5,63.0) and the CAM_5V via (34.2,49.325) sit inside the 3V3 fill. The 3V3 via (26.4,79.26) sits inside the
   RAW_PROTECTED fill. The round 27 ruling covers these: the I-5 lists say "include".
2. **U9 bypass.** These pairs would turn the board on with J400 open: U9.5–U9.6 0.200 mm, the BAT_IN track to U9.6
   0.200 mm, and J1.1's In2 ring and the BAT_IN via (17.5,87.15), each 0.251 mm from In2 RAW_PROTECTED. Already ruled
   (R25 safety observation 3).
3. **J440.1 onto J121.1.** §1 files this chafe under the OUT-to-GND class and says it fires by itself. J440.1 is
   PORT_4V8, so physically this is OUT to a rail that cannot sink (TPS7A91). Firing is possible but not certain. The
   statement errs conservative and is not shown false.
4. **Body-diode ratios.** The ratios 0.93–1.01× / ≥ 1.39× / ≥ 1.04× come from the severity check's wider
   1.043–1.137 A span. For the stated 1.063 / 1.128 A they are 0.945–1.003×, 1.417× and 1.063×. The stated ranges are
   outward bounds of these, so they are not false.
5. **S-8 table, J400.2 In1 GND.** The table says "0.250 since D-R20-05"; on `a0ec075e…` it is 0.551 mm, after
   D-R21-01. The table is labelled as the `50a39de5…` / D-R20-05 snapshot, GND is exempt there, and AGENTS states the
   current 0.55 mm rule.
6. **Two pairs the table does not list.** PYRO1_OUT to BUZZ_G is 0.510 mm: about 9 mA at most, no fire. Q124's gate
   to its own drain is 0.520 mm: the failed-short Q124 class. The table does not claim to be complete.
7. **BAT_FAULT_N to 3V3.** R89.2 is 0.175 mm from the 3V3 via under R89's own body. A bridge only masks U9's fault
   flag: a diagnostic loss.
8. **Sub-micron method differences.** I measured 0.5200 / 0.5001 mm against the recorded 0.5205 / 0.5008 mm (round
   28 ruling).
9. **Confirmations (observations 9–16 in the JSON).** AGENTS §2.4 networks, rule 4 probe topology, the rule 3 meter
   arithmetic, §1 distances, §1 arithmetic, S-8, per-flight procedures and the §2.5 sweep.

## Fix verification

| Item | Result | Verdict |
|---|---|---|
| R30-TRI-01 (ARM1_SENSE to U13.5) | 2.2049 / 2.1913 V and 0.1074 / 0.1087 mA at Vf 0.20 / 0.24 V; the BAT54 drop is ≤ 0.24 V at 0.1 mA; the text and its label match | confirmed |
| R30-TRI-01 sibling (EN load) | 11.2 kΩ ∥ (11.2 kΩ + 4 Ω) = 5.6 kΩ, stated | confirmed |
| R30-TRI-02 (chamber criterion) | Every current place says "every 85 °C part ≤ 85 °C" alone and records LS120's rise; the leftover "LS120 ≤ 70" strings are history marked as replaced; nothing generated is affected | confirmed |
| D-R29-01 (τ 47–58 µs) | Reproduced; same labelled phrase in the binding note (`c5cd0fa3…`, bound to `a0ec075e…`) and the docs | confirmed |
| D-R29-02 (test pins) | Pinned rule 4 text present in the binding note; the test was not run | partly |

## Limits

- Read-only: no `tools/check.sh`, no DRC and no gate seeds.
- No re-run of the transient or thermal models; their figures were checked for arithmetic and labels only.
- pcbnew shape distances at 0.5 µm resolution.
- Probe files are in `.supervisor/r31_safety/`.
