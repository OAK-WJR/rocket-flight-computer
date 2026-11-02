# R10 round 30 — requirements lens (Claude)

- Target commit `0afaed3`; board SHA-256 before and after: `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`.
- Totals (real errors only): **0 Critical / 0 Major / 0 Minor.**

## Findings

None. Every requirement in `docs/REQUIREMENTS.md` (F1–F12, P1–P3, M1, M3, the operating assumptions) was mapped to the
board and to `../../docs/VEHICLE.md`. No requirement fails on the board, no two requirements contradict each other, and
no number derived from VEHICLE.md is wrong.

## What was checked (observations, not counted)

- **MCU pin map.** All 100 U1 pad nets match `pin_table.tsv` `r10_net`, with 0 mismatches. This covers:
  - F10's ports and EXTI lines;
  - F5's SPI3 and the PD0 chip select;
  - F8's PC1 / PE4 / PC0 / PC5;
  - F6's PA6 and F11's PC14 / PB1;
  - PC3_C and PC13, which are NC;
  - VBAT on 3V3, so VBAT/4 reads 3V3.
- **F7 copper.**
  - The BAT_IN feed is 1.0 mm.
  - The IGN, OUT and RAW_ACT fire branches are 0.5 mm.
  - ACT_FET_S has exactly seven 0.4 mm segments.
  - The 0.4 mm RAW_ACT stub to TP120 and the sense / gate branches are not fire paths.
- **F8.**
  - The dividers and filters match the stated values (5.1 kΩ tops, 2 kΩ bottoms, 10 nF).
  - The cold-screen levels reproduce: 99.36 mV healthy, 146.2 mV open.
  - The one-fault figure of 3.342 V and Q122's 0.218 V reproduce.
  - Every terminal pin legend, terminal name and colour is present.
- **F9.**
  - D402 sits at B(4.45, 65.9).
  - The tap from J400.2 is 4.114 mm, and the GND via is 0.700 mm away.
  - BAT_SW_RETURN is {J400.2, R165.1, D402.1}.
  - The VLOGIC slew of about 166–196 V/s and the 21–26 ms 3V3 lead reproduce from TPS2121 Table 9-1 and the AP6320x UVLO and soft-start figures.
- **F6.**
  - The switch-network values match the board.
  - An independent EN model gives 10.34 ms at 6.0 V and about 8.05 ms at 5.71 V; the records give 10.3 / 8.07 ms.
  - The hold-up scaling at 470 µF and the PA6-trip hold-up of 0.103–0.164 ms and 0.291–0.430 ms reproduce.
- **F10.** The port regulators set 5.456 V and 4.792 V. The LR900-F's 1 W is the maker's maximum average consumption.
- **F1–F3.**
  - The ISM6HG256X datasheet figures match.
  - The drift, noise and ΔT allowance (4.5°, 0.030°, 9.04 °C) reproduce, as do the ISA apogee temperatures.
  - The accelerometer has 36.6 g against its 64 g range.
  - At 8.8 km MSL the pressure is about 316 hPa, above F3's 300 hPa.
- **P1 / P2.**
  - The outline is 46 × 90 mm.
  - The five supports are as stated, with no other holes.
  - The nearest exposed lands to (4, 44.3) are 3.808 / 3.860 / 3.881 / 3.989 mm.
  - The wire room is 5.003 mm, the same on both sides.
- **Board position.** The board's aft edge is at joint + 79.4–83.4 mm, 32 mm forward of joint + 47, which agrees with VEHICLE.md.
- **Storage, pack change, M1, M3.**
  - The drain is 0.84 mA, which flattens a 1 Ah pack in 7.1 weeks.
  - BAT_IN falls to 1 V in about 1.4 s, inside the 2 s wait.
  - The stock and cost JSONs match the text ($85.26, +$0.54 for the minimum purchase).
- **Temperature row.** The cold-end ratings of LED1, LED2 and LS120 and the MCU's θJA of 45.0 °C/W match the datasheets.
- **LS120's chamber pass criterion** (≤ 70 °C at a 70 °C chamber) is predicted to fail by the records' own Inference. That is consistent with the retained 55 °C limit and owner row 36, so it is not a contradiction.

## Fix verification

| Item | Verdict |
|---|---|
| R29-TRI-04: Temperature row, LS120 as a +70 °C part (80–92 / 65–77 / 48 °C, chamber criterion) | confirmed |
| R29-TRI-01: F9 labels (unclamped 7.5 / 9.6 V; R23-SAFETY-06; outcome (c)) | confirmed |
| R28 F8 / F9 relabels (cold screen, port-supply lead) | confirmed |
| R28-TRI-07: F4's hinge range of 64–84 % (spot check 81 % at 286 kPa, M 2.2) | confirmed (spot check) |
| D-R29-01 / -02 (generator rule 3, binding-note test) | not in this lens's documents |

## Coverage limits

- No DRC, route_check or check.sh was run.
- The flight-2 trajectory pairing behind F4 was not re-run.
- The envelope, chute Cd and masses were not re-derived.
- Not every part's temperature rating was re-read.
- J3's overhang was not re-measured against the HRO drawing.
- Probe scripts are in `.supervisor/r30_requirements/`.
