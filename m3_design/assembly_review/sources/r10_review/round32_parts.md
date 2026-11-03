# R10 round 32: parts lens

Target commit `3366287`, board `a0ec075e…` (SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`
before and after). Read-only; probes in `.supervisor/r32_parts/`.

## Totals

| Critical | Major | Minor |
|---|---|---|
| 0 | 0 | 1 |

## Findings

### R32-PARTS-01 (doc, Minor): the named "85 °C parts" leave out U3, Y1, both LEDs and the sixteen X5R MLCCs

**What the records say.**
- Owner row 33 (`docs/R10_VALIDATION.md:2494`): "The fitted 85 °C parts (MS5611, the AP6320x bucks, J430) therefore
  have no margin at a 70 °C bay."
- `docs/M3_R10.md:496`: "The 85 °C parts (MS5611, the AP6320x bucks, J430, the U4 alternates) then have no margin."
- `parts_qualification.md:40`: "the 85 °C parts (MS5611, AP6320x, J430, the U4 alternates) need bay air ≤ about
  55–60 °C".

**What the parts are rated.** These fitted parts are also rated to +85 °C at the hot end:

| Part | Rating | Source |
|---|---|---|
| U3, W25Q128JVSIQ (C97521) | −40…+85 °C | Winbond Rev G, p4; "I = Industrial (−40 °C to +85 °C)", p74 |
| Y1, NX3225GA-25.000M-STD-CRG-2 | −40…+85 °C | NDK sheet, STD-CRG-2 column |
| LED1, NCD0805R1 | −30…+85 °C | maker p1; also in parts_qualification.md:45 |
| LED2, KT-0805Y | −40…+85 °C | maker sheet |
| 16 X5R MLCCs: C6–C11, C19, C20, C22, C23, C28, C80, C89, C92, C95, C96 | −55…+85 °C | Samsung catalogue p5 (A = X5R) |

The same row 33 (Needed column) and ORDERING 8.3:608 already treat these as 85 °C parts:
- they log C6 / C7, C89 ("a BAT_IN X5R") and "near Y1 / U3";
- they offer "X7R parts on the same lands" as the remedy.

The general pass rule ("every 85 °C part ≤ 85 °C") is right. Only the named sets are false.

U1 (STM32H743VIT6, suffix 6) is not counted here. DS12110 Rev 8 Table 24 gives TA 85 °C at maximum dissipation,
105 °C at low dissipation, with TJ ≤ 125 °C, so its limit is set by junction temperature.

**Impact.** The owner-acceptance row understates which fitted parts have no hot-end margin. It leaves out the QSPI
log flash, the HSE crystal and all bulk X5R decoupling.

**Fix (text only).** In all three places, either list the full fitted set, or write "among them" and point to one
complete list in `parts_qualification.md`, beside the cold-end list.

## Fix verification

| Item | Verdict |
|---|---|
| R30-TRI-02: LS120 is no longer a chamber-test pass / fail gate | Confirmed. Every current place passes on "every 85 °C part ≤ 85 °C" and records LS120's rise. |
| R29-TRI-04: LS120 is a +70 °C part | Confirmed: MLT-5020 p2 item 6 gives −20…+70 °C. |
| R30-TRI-01: the bridge figures include the D120 / R131 pull-up (parts facts only) | Confirmed: BAT54A has its common anode on 3V3, and R131 is 10 k. |

## Observations (not counted): 10

- BOM, CPL and board fields agree:
  - 81 codes and 206 designators, each listed once;
  - every quantity matches its designator count;
  - LCSC, MPN and footprint agree on every part;
  - C84 is on the owner BOM only.
- Every BOM comment decodes from its MPN. The UniOhm multiplier codes give R164 = 2.2 Ω and R166 = 0.36 Ω.
- `jlc_orient --verify-cpl`, re-run read-only, gives 67 + 125 rows rebuilt, worst residual 0.491 mm, no errors and 14
  placement-only rows.
- The cost record's arithmetic reproduces: $85.26 per board, $16.79 fixed fees, 45 Extended codes.
- Voltage ratings, MOSFET VGS and IC input maxima are respected at the actual operating points.
- Pin maps re-read against the datasheets for TPS7A91, TPS2121, TXU0202, TPS709, TPS25947, BAT54A and AONR21357
  match the board.
- These recalculated figures reproduce:
  - the TPS2553 camera limit, 1.041–1.249 A;
  - U9's minimum current limit, 3.946 A;
  - the fire currents;
  - the CRM2512 pulse figures;
  - the C126 tail, IWDG timing and R92 / R166 corners;
  - the D402 EN shift, C123's τ and C84's endpoints.
- L400 (6.8 µH) differs from the DS41326 table's 10 µH, but it is sized by the datasheet's own equation. The table is a
  recommendation, not a limit.
- BAT54A's EasyEDA land is the 1.6 / 2.8 mm SOT-23 variant (0.235 mm residual). The cached JSCJ sheet has no package
  drawing, so no land error is shown.
- LS120 is driven within its 2–4 V operating range. Its current qualification is already disclosed as open.

## Coverage limits

- Datasheets came from the PDF cache; there was no live supplier access.
- The DB125 wire-entry side and LED polarity marks are left to the factory preview.
- IMU and MCU pin facts belong to the mcu lens.
