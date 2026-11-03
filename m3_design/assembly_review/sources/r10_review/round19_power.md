# Round 19 power review (Claude)

Target commit `acba1969b42973aaf8d348dc6d2fce6b465fc1dd`. PCB SHA-256
`a3144b151b58daf8ba5747def50decc4d1751ad35be478fafc89ef53aa533918` before and after the review.
**Result: 0 Critical / 0 Major / 1 Minor (new).** [Structured evidence](round19_power.json).

Scope: battery entry to every rail (U9, R166, C88 / C84, VLOGIC, 3V3 / 3V3A, PORT_5V3 / PORT_4V8, camera switch,
RAW_ACT and the R134 fire path), the round 18 fixes that touch power, IPC-2152 widths, via counts, thermal reliefs and
hot-plug / brown-out behaviour against the maker limits.

## Finding

**R19-PWR-01 (Minor, new): several power feeds change layer through a single 0.3 mm via, including the only
battery-path input of the logic supply.** Measured per outer-layer copper island on the native board:

| Net | Pads fed | Single via (mm) | Current through it (DC solve) |
|---|---|---|---|
| RAW_PROTECTED | U11.2 (TPS2121 IN2, the only battery input of VLOGIC), C97.1 | (24.3, 66.0) | 100 % (1.00 A of 1.0 A) |
| PORT_5V3 | U402.1 (camera switch), C430.1 | (42.0, 61.8) | 1.25 A at the U402 limit |
| PORT_5V3 | U401.9 / .10 (LDO IN), C405.1 | (25.9, 8.6) | – |
| PORT_5V3 | U401.7 (TPS7A91 EN, no defined pull) | (25.65, 14.9) | – |
| PORT_4V8 | U401.1 / .2 (LDO OUT), C406.1 | (29.75, 12.6) | 0.60 A of 0.6 A |
| VLOGIC | C84.1 (470 µF hold-up) | (29.5, 82.05) | 100 % |
| 3V3A | U1.20 / .21 (VREF+ / VDDA), C21, C22 | (27.0, 49.25) | – |
| 3V3A | R164.2 and the IMU / barometer island | (16.0, 50.2) | – |

Current capacity is not the problem. The IPC-2152 internal fit applied to the 0.3 mm / 20 µm barrel, with no plane
credit, gives about 8 °C at 1.25 A and about 19 °C at U11's 2.0 A maximum limit. The problem is that each via is a
single point of failure:

- An open or cracked via at (24.3, 66.0) removes battery power from the primary computer; recovery then falls to the
  Blue Jay.
- An open via at (29.5, 82.05) silently removes the 470 µF hold-up: ride-through falls to roughly 0.03–0.2 ms on
  C6 / C7 alone (Calculation).
- The others drop the camera, both GPS and radio (the LDO's EN would float), VDDA / VREF+, or the sensors.

By contrast, U9 OUT and U400 IN each have two vias, and the 3V3 output has two independent paths. The U9 IN feed is
one 1.0 / 0.5 mm via by design (the C88-first hot-plug topology). R18-GATE-03 pinned only the U9 transitions; this is
the board-side inventory.

At U11 the space is tight: the VLOGIC trunk, C99.1 and ACT_EN_MCU on F.Cu crowd the pad, and the In2 3V3 finger
lies west of the RAW strip. No legal octilinear spot for a second via was found within about 1 mm, so this is a
respin item.

**Fix:** now, without CAD:

- add first-article steps for a pack-only power-up (USB disconnected) and a C84-connected check (VLOGIC capacitance
  at TP83, or a measured hold-up);
- list these eight transitions with their currents in R10_VALIDATION deviation section 4;
- extend the R18-GATE-03 pin to them.

At the next board change, add a second via (or a second outer-layer path), U11.2 and C84.1 first.

## Round 18 fix verification (power side)

| Decision | Verdict | Measured |
|---|---|---|
| D-R18-06 (In2 3V3) | confirmed | One outline, 1466.52 mm² (was three, 1447.88 mm²). Deflation bisection on the unfractured fill gives island A to main 0.5495 mm at about (26.92, 61.98), and the finger's internal pinch 0.4745 mm at (23.46, 67.83), against a recorded "about 0.50". The pinch sits beside the GND via (22.825, 67.825); the cross-section there is about 0.75 mm in total. L1.2 → R164.1 is 9.99 mΩ (was 32.83), L1.2 → U1 VDD 7.38 mΩ (was 16.40). The neck rise is ≤ 0.4 °C. Side effect not in the record: the former sense-only finger now carries 57 % of the 3V3 load (0.23 A of 0.4 A); U2's FB via (23.2, 68.6) sits on it, a shift of about 1 mV. Return path: In1 GND is one piece underneath, and only DC / slow B.Cu nets cross the new In2 boundaries. |
| D-R18-04 (power side) | confirmed | RAW In2 one outline, 1222.74 mm²; In1 GND one outline, 3753.40 mm². U9 → U400 is 37.77 mΩ (R18: 38.02); the 1.05 mm B.Cu neck rises 7.8 °C at 1.9 A. U9 → U11 is 7.05 mΩ. |
| D-R18-01 (power side) | confirmed | R62 / R63 are absent, U1.18 is NC, VBAT (U1.6) is on 3V3 and R123 is 2 kΩ (PC1 sources 1.1 mA). A new 1.69 mm² F.Cu GND fill piece hangs only on the U1.19 (VSSA) pad and carries no current. |
| D-R18-02 (power side) | confirmed | The 4.744 V bound is reproduced on its 6.0 V basis. At the fire budget's own four-stall BAT_IN (5.73 V), \|VGS\| is 4.52–4.62 V, still above the 4.5 V point where AONR21357 RDS(on) ≤ 12.3 mΩ is specified. |
| D-R18-03 (power side) | confirmed | U11.12 is the TPS2121's only ground pin. It now reaches the GND via (26.384, 67.444) through C99.2, about 2.4 mm of 0.3 mm track, carrying quiescent current only. |
| D-R18-08 (L400 land) | confirmed | 2.0 × 1.8 mm pads at (21.95, 5.55) and (26.45, 5.55) match Bourns' layout (6.50 / 2.50 / 1.8). PORT_SW is 2.61 mΩ; L400 → U402 is 36.12 mΩ (was 36.07). The inductor's Isat of 4.3 A exceeds the AP63201's 3.1 A peak limit. Copper DRC is 0. |
| D-R18-09 (power side) | confirmed | The new R430 is the same 22.6 kΩ 1 % 100 ppm part value, so the camera limit stays 1.041–1.250 A. C84 is still on VLOGIC (via: R19-PWR-01). |
| D-R18-05 (fire copper) | confirmed | IGN is 0.5 mm × 10.523 mm, OUT 0.5 mm, the RAW_ACT fire run 0.5 mm, with seven 0.4 mm source bridges and a 1.0 mm BAT_IN feed. There is no via in the fire path. The GND fire return is 0.88 mΩ. |

## Closed without a finding

- **U9 latch-off.** TPS259470L latches only on thermal shutdown; overcurrent is actively limited. Its settings check
  against SLVSFC9C: ILIM 3.96–4.84 A, UVLO 4.96 / 4.51 V, OVLO 9.77 V (OVLO pin 1.03 V at 8.4 V), dVdt 0.43 V/ms,
  EN / OVLO resistors ≥ 350 kΩ.
- **TI's "2 × full load" guideline.** About 38 °C at 4 A on the 1 mm neck (long-conductor fit, no plane credit); the
  runs are 1–4 mm long.
- **Hot-plug inputs.** They are byte-identical to the previous board's apart from the board hash.
- **Port buck and LDO thermals.** The radio's maker figure is 200 mA average at 27 dBm, against the 0.30 A allocation.
- **J1.2 relief spokes.** These follow the house THT rule.
- **VBAT/4 as the 3V3 monitor.** Its ±10 % ratio error is worse than VDDA from VREFINT plus the R164 drop: a firmware
  note only.

## Executed

- Native pcbnew 10.0.7 dumps and a board-to-board copper diff against `632a9ad3`.
- Zone and island inventory.
- Neck bisection by polygon deflation.
- 15 runs of `tools/dc_solve.py` (the committed version): 14 on the current board, 1 on the previous one.
- A via-feed inventory.
- In2 reference sampling under B.Cu.
- kicad-cli 10.0.7 DRC on a copy: 0 copper violations, 0 unconnected.
- A hot-plug input diff.
- Recomputation against the maker tables (TI TPS25947, TPS2121, TPS7A91 and TPS2553; Diodes DS41326; Bourns
  SRP5030T; AOS AONR21357; MicoAir LR900-F).

Probe files are in `.supervisor/r19_power/`.

## Limits

No physical, transient-SPICE or thermal simulation. The DC solves assume room-temperature copper and 20 µm plating.
The hot-plug model was not re-run, because its inputs are unchanged. Converter stability with the moved FB point is
inference. The second-via spots at U11 were screened geometrically, not by a seeded DRC. Records edited in the
worktree after `acba196` were not reviewed.
