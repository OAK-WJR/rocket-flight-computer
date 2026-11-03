# Round 25 MCU review (Claude)

Target commit `c4bb56b`. PCB SHA-256 `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f` before and after.
**Result: 0 Critical / 0 Major / 1 Minor.** Evidence: [round25_mcu.json](round25_mcu.json); probe scripts in
`.supervisor/r25_mcu/`.

## Finding

**R25-MCU-01 (calc, Minor): rule 8's hold-up "after the PA6 trip" is computed from 5.3 V, above the trip window that
the same rule states.**
- **What it contradicts:** rule 8 puts the trip at VLOGIC about 4.8–5.2 V (PA6 0.44–0.47 V, so 0.44 × 11 = 4.84 V to
  0.47 × 11 = 5.17 V, with R60 100 k / R61 10 k on the board). It then quotes hold-up "after the trip" of 0.157–0.182 ms
  with all ports on and 0.44–0.48 ms with the camera off, "from 5.3 V at 300.8 µF". M3_R10 line 616 also says "from the
  trip at about 5.3 V".
- **Where:** binding note obligation 43, M3_R10 lines 616 and 1017–1018, REQUIREMENTS F6, ORDERING line 674, and
  R10_VALIDATION rows 5 and 25.
- **Calculation** (`holdup.py`, constant power from `parts_budget.json`, C84 counted as 300.8 µF, down to 3.8 V): it
  reproduces the records exactly from their own inputs. From the stated window the hold-up is:

  | Trip point (VLOGIC) | All ports on | Camera off / shed |
  |---|---|---|
  | 5.17 V (window top) | 0.141–0.164 ms | 0.397–0.430 ms |
  | 4.84 V (window bottom) | 0.103–0.120 ms | 0.291–0.315 ms |
  | 5.3 V (the records) | 0.157–0.182 ms | 0.441–0.478 ms |

  - The stated minimum overstates the window's worst case by 52 %.
  - Even a 1 % divider spread puts PA6 = 0.47 V at no more than 5.26 V.
- **Impact:** the owner's open hold-up question (row 25) and the shedding latency are judged against figures up to
  about 1.5 × too long.
- **Fix (text only):** "0.10–0.16 ms with all ports on and 0.29–0.43 ms with the camera off / shed (Calculation, from
  VLOGIC 4.84–5.17 V at 300.8 µF)".
  - Make the change in `r10_sch_check.py` rule 8, then regenerate the binding note and update its test.
  - Make the same change in M3_R10 616 / 1017, REQUIREMENTS F6, ORDERING 674 and R10_VALIDATION rows 5 / 25.

## Fix verification

| Change | Verdict | Measurement |
|---|---|---|
| D-R24-19 rule 4 | confirmed | Q120's gate drive has two parallel barrels, (16.2,73.3) + (15.4,72.85). Q121's has two, (11.14,71.7) + (11.74,72.3). The probe point R120.2 / C120.2 is on ACT_GATE. |
| D-R24-19 rule 5 | confirmed | R91.1 has the 3V3 vias (28.1,60.0) + (28.1,59.4). U1.28 has the LOGIC_SOURCE_ST vias (30.85,51.8) + (30.45,51.4), linked on both layers. |
| D-R24-19 rule 8 | confirmed (the corner) | Turn-off corner 4.802 V, or 4.778 V without D402. 0.44 × 11 = 4.84 V. The hold-up sentence is R25-MCU-01. |
| D-R24-19 obligation 17 | confirmed | EN is 1.4015 V at 6.0 V. The drop-out is 10.35 ms. Windows: on 4.72–5.25 V, off 4.29–4.80 V. |
| D-R24-18 | confirmed | BAT_FAULT_N (PA5) is 0.200 mm from the EN via at its legs and 0.2015 mm at the chamfer. |
| D-R24-21 | confirmed | BOOT0's second via is cited as D-R24-03 everywhere. |

## Observations (not counted)

- **U1 pin map.** All 100 U1 pads match pin_table `r10_net` / `mode_af`, the binding note and the netlist. The pad order
  follows DS12110 Rev 8 Figure 5.
- **Datasheet checks.** These were spot-checked against Tables 9–14:
  - the alternate functions, the ADC channels and the I/O structures;
  - PC1's TRACED0 / RTC_TAMP3 / WKUP5.

  The cited pages are correct.
- **Binding-note hashes.** Board, netlist, pin table and circuit all match the committed files.
- **Ports.** Port UART directions are correct, including the camera path through U12 (TXU0202 Table 6-1).
- **Copper behind the other obligations matches the text:**
  - pulls and dividers (/11, /11.2, VBUS / 2);
  - R123 / R127 hold-off;
  - U5 at 0x77;
  - VREF+ = VDDA, VBAT = 3V3;
  - IMU INT1 on PE1.
- **IWDG.** 960 LSI cycles gives 28.571–32.653 ms (Table 146).
- **PA4 / PA5.** Table 120 allows no injected current on PA4 / PA5. They are open-drain inputs pulled up to 3V3, and no
  injection path was found.
- **Not judged here.** Hole-to-hole spacing of the 0.566 mm parallel-via pairs is the manufacturing lens's item.

## Coverage limits

- AN2606 and RM0433 were not re-read.
- The AF tables were spot-checked, not read column by column.
- The load-power model is the records' own.
