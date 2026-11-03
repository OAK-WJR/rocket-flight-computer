# R10 round 24: requirements lens

Target commit `f2b8251`, PCB `1407e8506efbac0f664b3aeb65568c32ae9670c9b45b502a465cba1130de522e` (SHA-256 the same
before and after this review). Every requirement in `docs/REQUIREMENTS.md` was mapped to the board after the round 24 board
pass, including M2's 45° rule and the F8 / F9 J400 network with D402. Probe files are in `.supervisor/r24_requirements/`.

**Totals: 0 Critical, 0 Major, 4 Minor.**

## Findings

| ID | Kind | Severity | What is wrong | Fix |
|---|---|---|---|---|
| R24-REQUIREMENTS-01 | calc | Minor | F9 / D-R24-11 say "the EN timing figures stand". They do not, under the record's own 50 nA bound for D402. D-R20-11's ±0.1 µA is U9's own EN leakage, so D402's current adds to it. During a J400 drop-out, D402 drains C87 through R165 with its full current (50 nA at EN, not 25 nA). The D-R20-11 model reproduces exactly without D402 (6.58 / 8.50 / 10.65 / 20.47 / 26.41 ms, 5.917 V, 30.3–128.6 ms). With D402 it gives 6.30 / 8.20 / 10.35 / 20.11 / 26.02 ms at 5.5 / 5.73 / 6.0 / 7.4 / 8.4 V, a pack ≥ **5.956 V** for the 10 ms criterion (was 5.92 V), and turn-on 30.4–130.3 ms. | Restate the figures in F4 / F6 / F9 / Accepted risks / AGENTS / M3_R10, or cite a maker leakage maximum at ≤ 5.3 V that makes the change negligible. |
| R24-REQUIREMENTS-02 | doc | Minor | M1 quotes `stock_check.json` 2026-10-31T23:23Z with U9 at 40 in stock and −69 orderable. The committed file is the 2026-11-02T01:42:53Z run, with U9 at 28 / −83 / minimum 7 and U4 at 9 / 2. M3 and M3_R10 already use the new run. | Update M1's timestamp and U9 figures. |
| R24-REQUIREMENTS-03 | calc | Minor | P3: at 8.0 m/s with 20 mm of crush, the load is 64 / 0.04 = 1600 m/s² = **163 g**, not 168 g. 168 g needs 8.11 m/s; the source used 6.1–8.1 m/s. The same text is repeated in ORDERING 8.4 and R10_VALIDATION rows 12 and 32. | Write 98–163 g, or use 6.2–8.1 m/s. |
| R24-REQUIREMENTS-04 | doc | Minor | P2 gives the J2 lands as 3.871 / 3.918 mm from the (4,44.3) support. Those are distances to the round TC2030 pads' bounding squares. The round Ø0.787 mm lands are at **3.880 mm (J2.1, 3V3) and 3.987 mm (J2.3, NRST)**, so the range is 3.808–3.987 mm. The error is conservative; the nylon-hardware conclusion stands. | Correct the figures in P2, M3_R10, R10_VALIDATION, ORDERING 8.4 and R10_VEHICLE_HANDOFF. |

## Fix verification

- **D-R24-17 (M2 45° rule): confirmed.**
  - An independent scan finds 0 uncovered 90° bends on `1407e850…`. The 35 right angles left are at pads or vias, each with its inner corner covered.
  - The scan finds 59 such bends on `5516eeec…` (F.Cu 25, B.Cu 31, In2 3), the same split as D-R24-17's record.
  - No off-angle segments and no arcs.
  - route_check on a copy: 0 failing, 5 unrecorded noncritical leftovers.
  - Seeds: a plain 90° bend fails `right_angle`; an overlap-only corner fails `dead_copper`.
- **D-R24-11 (F8 / F9, D402): partly.**
  - D402 is a C535146 ESD103-B1-02EL at B(4.45,65.9).
  - BAT_SW_RETURN's pads are exactly {J400.2, R165.1, D402.1}, and D402.2 is on GND.
  - The tap is 4.114 mm, ahead of R165, and the GND via is 0.7 mm away.
  - BOM (9 pieces) and CPL agree.
  - The 5.7 mV, 14 mV and 7.5 V figures reproduce. The timing claim does not (finding 01).
- **D-R24-13 (order-number placeholder removed): confirmed.** No placeholder text remains on the board.
- **Second vias, R92 and TP88 as they bear on F7 / F8 / M2: confirmed.**
  - The fire-path widths are unchanged.
  - Only U401.11's two vias are in an SMD pad.
  - Silkscreen text is ≥ 1.0 mm.
  - check_r10 on a project copy passes every rule except S-4 and K-binding. Those two need the schematic and the binding note beside the copy.

## Observations (not counted)

There are 10, all in the JSON. The main ones:

- BUZZ_G's T at (20.5, 58.70) is now 0.02 mm from its chamfer. route_check does not count it, because its short_segment test works on whole tracks.
- F1's 9 °C allowance is still computed for 30 s; at 35 s it is about 7.75 °C. The recompute is disclosed as open.
- M3's top cost figure with the minimum purchase and the handling fee is $105.92, against "about $102–$105".
- D402 covers J400.2 only. A discharge into J400.1 with the switch open reaches only R80 and BAT_IN, not EN.

## Limits

- No full check.sh, DRC or ERC run.
- Firmware-only requirements were not judged.
- The hot-plug, plate and fit models were taken as recorded.
