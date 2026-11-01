# Round 22 safety review (Claude)

Target commit `ec8cb98c198e25462a2fb5d34f87a84636e37993`, PCB `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1`
(the same before and after this review). **0 Critical / 0 Major / 1 Minor** (1 new).

No single fault fires the e-match while the bus is disabled. With the bus enabled the recorded single faults still fire:
OUT to GND (0.1768 / 0.1795 mm), Q124 gate to drain (0.5195 mm, in the package), a failed-short Q124, the 3V3 via 0.676 mm
from R128.1, FMEA I-5 and C128. Round 21 added no non-GND neighbour to any pyro or arming net. The only new neighbours are
GND, RAW_PROTECTED and BAT_FAULT_N copper at the moved R81 / C87, and every one of them fails safe. D-R21-01, -02, -04 and
-05 measure as claimed. The one finding is a records defect.

## Method

- **Inputs.** The committed tree (`git archive ec8cb98`), plus the previous boards `0dc84776…` and `a3144b15…` for diffs.
- **Geometry.** Native pcbnew export, analysed with my own numpy code. The checked claims were re-measured with pcbnew shape
  collision.
- **S-8 two ways.** Native polygons, and my own parser of the committed fabrication Gerbers (In1 / In2 with net
  attributes) and the PTH drill file. The two agree.
- **Gates on a probe copy.**
  - kicad-cli 10.0.7 DRC, all severities, with schematic parity: 0 / 0 / 0.
  - check_r10: S-1…S-9, K-actuators, K-power, K-rules, K-plane, F9-1 and K-binding all OK.
  - route_check r10: 0 failing.
- **Seeds.**
  - The previous board fails K-power five times (R81.1 / C87.1 single vias, and U2.1).
  - Removing the BAT_ENABLE keep-out at (17.1,82.8) and refilling makes S-8 fail at 0.251 mm.
- **Fault analysis.**
  - Adjacency inventory of 18 pyro, arming and load-switch nets (outer ≤ 0.5 mm, inner ≤ 1.0 mm), diffed against
    `0dc84776…`.
  - Single-open graphs for EN and the nine gate-to-bias paths.
  - GND returns of 19 pull-down and fire-return pads.
  - An I-5 inventory (3V3 / 3V3A against 18 nets above 4 V, barrel walls included).
  - EN timing and peak from TI SLVSFC9C.

## R81 / C87 at U9's end (D-R21-05)

- **Single opens between U9.1 and R81: 4** (13 on `0dc84776…`), 3.890 mm in all:
  - the via (17.10,82.80);
  - B.Cu (17.1,82.8)–(17.6,82.3), 0.707 mm;
  - F.Cu (18.023,81.877)–(17.1,82.8), 1.306 mm;
  - F.Cu R81.1–C87.1, 1.877 mm.
- **C87.1: 3** (14 before).
- **Any other copper open leaves EN on R81, so EN is held low with J400 open.** That covers the 12 objects on the switch run
  and R81's GND return, which is the F.Cu GND piece with vias (20.2,81.0) and (20.85,76.4), so no single via can cut it.
- **Each of the 4 opens also cuts J400 off from EN.** The board then stops following the switch, which shows at the next
  switch operation.
- **Part-level exception:** an open R81 (body or joint). EN then floats on C87. After a closed-switch check, opening J400
  leaves the board on, which the per-flight "opening J400 turns it off" check catches.

| New neighbour (F.Cu) | Gap (mm) | If it shorts |
|---|---|---|
| R81.1 (EN) – GND via (17.2,79.9) | 0.1732 | EN held low, U9 off |
| R81.1 – GND track (15.875–17.2, 79.9) | 0.2232 | EN held low, U9 off |
| R81.2 (GND) – RAW_PROTECTED via (20.3,79.1) | 0.3068 | U9 output short: U9 limits and latches off |
| C87.1 (EN) – GND fill | 0.2505 | EN held low, U9 off |
| C87.2 (GND) – BAT_FAULT_N track | 0.2536 | Reads as a U9 fault |

The GND vias (20.706,65.619) and (16.639,63.939) are gone; they were 0.1951 mm and 0.2085 mm from RAW_ACT.

## EN network

**S-8 keep-outs and spacing.**
- In2 copper is 1.050 mm from all three BAT_ENABLE vias.
- In1 GND is 0.2505 mm (exempt).
- D-R19-02: the via (19.675,66.6) is 0.500 mm from R134.2 (pcbnew); the re-bent hop is 0.650 mm.

**D-R19-10 values.** R80 / R165 470 kΩ (C23178), R81 300 kΩ (C23024) and C87 220 nF X7R (C21120), in the netlist, the BOM and the CPL.

**EN timing** (Calculation; SLVSFC9C p9 thresholds, IENLKG ±0.1 µA, 1 % resistors, C87 0.72–1.27×):

| Pack | Turn-on, nominal / worst (ms) | Drop-out immunity, worst (ms) |
|---|---|---|
| 8.4 V | 44.7 / 30.3–60.8 | 26.41 |
| 7.4 V | 55.5 / 37.3–76.7 | 20.47 |
| 6.0 V | 87.7 / 56.6–128.6 | 10.65 |
| 5.73 V | 100.4 / 63.6–152.8 | 8.50 |
| 5.5 V | 116.1 / 71.5–188.8 | 6.58 |

The 10 ms criterion needs a pack of at least 5.917 V. Time constants are 50.0 ms (charge) and 66.0 ms (discharge).

**EN peak.** The EN/UVLO limits are 6.5 V absolute maximum (p7) and 5 V recommended (p8).
- With C87 beside R81, no copper open can charge C87 above the divider: at most 2.086 V at 8.4 V, with tolerance and
  leakage.
- A 12.6 V pack gives 3.12 V.
- The 19.9 V D8 clamp gives 4.91 V, and that is filtered by τ 50 ms.
- One shorted top resistor gives 3.33 V.
- All of these are inside both limits.
- An open R81 lets EN rise toward BAT_IN through 940 kΩ, at no more than 9 µA. TI permits this: p8 note 2 asks for a
  pull-up of at least 350 kΩ when the supply is above 5 V.

## S-8 and the new 0.55 mm PTH rule (D-R21-01)

| Barrel | In1 | In2 |
|---|---|---|
| PYRO1_OUT via (11.630,55.100) | GND 1.0209 | GND 1.0209, 3V3 2.698 |
| J121.1 | GND 1.050 | GND 1.050, 3V3 1.0612 |
| J121.2 (rings kept) | wall 0.5505, ring 0.2501 GND (exempt) | same |
| ACT_GATE vias (16.2,73.3), (11.14,71.7) | GND 1.050 | RAW_PROTECTED 1.050 |
| BAT_ENABLE vias (×3) | GND 0.2505 (exempt) | RAW_PROTECTED / 3V3 1.050 |
| J400.2 | GND 0.2505 → **0.5505** (exempt) | GND 1.050, RAW_PROTECTED 1.050 |

- **Least non-exempt gap:** 1.0209 mm. S-8 holds at every barrel and ring.
- **J1.2:** In2 RAW_PROTECTED 0.2505 → 0.5505 mm.
- **J3 slots:** 0.4505 → 0.5505 mm.
- **Every other plated pad:** unchanged.
- **Fill pieces:** unchanged in count.

## Arming nets on the AUD-2 list (owner row 30)

The partner GND via distances are:
- BAT_ENABLE: 1.866, 1.875 and 2.902 mm;
- BAT_SW_SOURCE: 7.467 mm.

The partner-via and one-region rules protect the return path of fast edges. These nets carry at most 18 µA, set by the
470 kΩ resistors. EN is 227 kΩ ∥ 220 nF, now 2 mm from U9.1. In1 GND shields the B.Cu hop from the F.Cu RAW_ACT / ACT
corridor.

**The exemption is physically sound.** One wording point: "τ ≈ 50 ms" describes BAT_ENABLE only. For BAT_SW_* the reason is
the 470 kΩ current limit. route_check counts only BAT_ENABLE's short_layer_hop of 2.973 mm.

## Finding

**R22-SAFETY-01 (Minor, new). Section 1 of the deviation list was not carried to `5516eeec…`.**
- **Stale row.** R10_VALIDATION §1 still lists "R134.2 (RAW_ACT) to the GND via (20.706,65.619), 0.196 mm, about 23 A
  unfused". D-R21-05 removed that via.
- **Least RAW_ACT gap.** The least RAW_ACT-to-GND pad / track / via gap is now 0.300 mm, B.Cu RAW_ACT (22.8,61.4)–(22.8,63.875)
  to U11.6. D-R21-05 says 0.302 mm. Fills stay at 0.2505 mm.
- **Wrong minimum.** The stated minimum, "0.173 mm (R129.1)", is not the board's least protected-net pair. That pair is
  ARM1_SENSE to U13.5 (CAM_IO_3V3) at 0.150 mm. It is benign: at most 3.3 V on PC5 and about 0.15 mA in the match. It is
  also present on `a3144b15…`.
- **Missing rows.** The D-R21-05 neighbours in the table above are absent from §1.
- **Fix (text only).** Mark the row as removed and give 0.300 mm. Add the D-R21-05 neighbours. Restate the minimum together
  with its net set. Read 0.300 for 0.302 in D-R21-05.

## Fix verification

| Fix | Verdict | Note |
|---|---|---|
| D-R21-01 | confirmed | J1.2 / J400.2 0.5505 mm, J3 0.5505 mm; S-8 ≥ 1.0209 mm; native = Gerber |
| D-R21-02 | confirmed | No pyro / arming neighbour. One new I-5 adjacency: 0.475 mm to U2.2, not below the existing 0.400 mm pin pair |
| D-R21-03 | confirmed | battery_entry note matches the netlist |
| D-R21-04 | confirmed | route_check 0 failing; exemption sound |
| D-R21-05 | confirmed | 4 single opens (13 before); neighbours fail safe; EN ≤ 2.086 V. The figure 0.302 should read 0.300 mm |
| D-R20-01 | partly | 1 via + 3 segments remain (owner row 29) |
| D-R20-05, D-R20-11, D-R19-02, D-R19-10, S-8 keep-outs | confirmed | Figures reproduce; the keep-out seed fails S-8 |

## Fix now

1. **R22-SAFETY-01.** The R10_VALIDATION §1 edits above. Text only, no board change.

## Closed, not filed

- **U9 bypass.** BAT_IN–RAW_PROTECTED at the J1.1 ring (0.2501 mm), the via (17.5,87.3) (0.2505 mm) and U9.5–U9.6 (0.200 mm).
  I agree with rounds 20 and 21: it needs a hard short.
- **I-5: not worse.** The new run does not lower the 0.300 / 0.2501 mm minima. The route list omits the U2.1–U2.2 pin pair
  (0.400 mm) and four 0.2505 mm barrels. AP63203 EN may be left open at a respin (Diodes DS41326 p2).
- **C128: not worse.** It is a Murata GCJ soft-termination part.
- **IGN to GND with the bus on.** R134 sees about 34 W until it opens; there is no fire path.
- **ESD into J400.2.** At worst a brief U9-on of about 79 ms; no fire path.
- **Q124 gate pin-to-first-node segments.** Inherent.

Full evidence: `round22_safety.json`. Scripts and outputs: `.supervisor/r22_safety/`.
