# Round 23: mechanics (Claude)

Target commit `c70d261`. Board SHA-256 before and after: `5516eeec…f9d315a1` (unchanged). Totals: **0 Critical, 0 Major, 4 Minor**.
Angle: flight physics (thrust curves, vibration, landing, harness, bay temperature). Machine-readable twin: `round23_mechanics.json`. Probes: `.supervisor/r23_mechanics/`.

## Flight loads from the motors (Calculation; vehicle mass and Cd are Inference)

1-D trajectories from the thrustcurve.org cert curves ([K850DM](https://www.thrustcurve.org/motors/AeroTech/K850DM/), [HP-L1000W](https://www.thrustcurve.org/motors/AeroTech/HP-L1000W/)), airframe 1.5–2.7 kg without the motor:

| | K850DM | L1000W |
|---|---|---|
| Peak sensed axial | 25.8–35.1 g | 27.7–37.2 g |
| Coast after burnout | −4.7 to −10.7 g | −6.4 to −13.2 g |
| Max Mach | 1.18–1.60 | 1.58–2.07 (1.93 at 1.8 kg) |
| Apogee | 4.0–4.2 km | 5.6–5.8 km |

These match the recorded 28–37 g. Boost, coast and deployment (cord snatch 3–12 g, opening at 40 m/s about 22–45 g; Inference) all act **in the board's plane**, so they don't bend the board. The transverse 100 g plate case is really a landing case.

## Findings

- **R23-MECHANICS-01** (Minor): no 18 or 16 AWG lead can make its 90° turn in the wire room.
  - A lead turning from radial to axial needs exit + inner bend radius + OD of radial room. The room is 5.003 mm on the bare bore, or 4.493 mm with P2's wall allowance.
  - At an inner radius of 1 × OD, 22 AWG needs 3.9 mm and 20 AWG 4.1 mm. 18 AWG needs 5.1 mm and 16 AWG 5.7–6.5 mm.
  - At 2–3 × OD (common practice is 3 × OD) no gauge fits.
  - OQ-1 / P2 accept 16–22 AWG and ORDERING allows 28–16 AWG. R9 had 6.4–7.0 mm of room and a "≤ 22 AWG, bend within 2 mm" rule; R10 dropped that rule.
  - Also: M3_R10's "4.503 mm" should read 4.493 mm.
  - Fix (docs only): cap leads at 20 AWG, OD ≤ 1.8 mm, ferrule protrusion ≤ 0.5 mm, and bend at the wire face.
- **R23-MECHANICS-02** (Minor): the 6 m/s landing speed has no source.
  - Descent mass is the airframe plus the spent case (817 / 794 g): 2.3–3.5 kg.
  - Under the 36″ chute at Cd 1.5 that gives 6.1–8.1 m/s, so 95–168 g at 20 mm crush.
  - The plate model, run unmodified, puts C431 on a 4 mm sled at **125 g** (D5) / 250 g (D10), C421 at 133 g and C411 at 175 g.
  - The strain on these 1210s reaches 1.2–2.2 millistrain at those loads.
  - Fix (no board change): a sled relief pocket under C411 / C421 / C431, or 4.5 mm standoffs with a plate ≤ 0.8 mm. Also root the landing g in the chute.
- **R23-MECHANICS-03** (Minor): part ratings are compared with bay air, not with the board.
  - The project's own 10–15 °C/W at a 1.0–1.5 W pad load puts the board 10–22 K above the bay air.
  - A sealed bay adds another 2.5–10 K over a 30–60 min hold.
  - At the 70 °C limit, these fitted parts have no margin: the MS5611 (85 °C, TE p1), the AP6320x bucks U400 / U2 (TA 85 °C, DS41326 p4) and J430 (85 °C). Nor would the 85 °C U4 alternates.
  - With margin: the ISM6HG256X (105 °C), C84 (105 °C) and U9 (TJ 125 °C).
  - Aero heating is **not** the driver. At Mach 1.93 the recovery temperature is 196 °C. The inner wall reaches 88 °C under the single 1.6 mm tube (hot start), but bay air rises only 0.4 K.
  - Fix (docs, bench and firmware rule): log the MS5611 / U4 / buck temperatures in the 70 °C chamber test, and add a pad temperature announcement.
- **R23-MECHANICS-04** (Minor): R10 defines no battery-lead route.
  - J1 is the forward-most west terminal (pads y 74.1 / 77.6) and the pack is aft.
  - The top-side path runs past the J121 and J400 exits (the J400.2 chafe class), the (4,44.3) support head and J3. That is the path the records forbid for J440.
  - The only explicit route, below the sled, is R9's.
  - Fix (docs only): route below the sled and round the forward edge into J1; give each terminal a tie point; anchor J121's leads at the bulkhead.

## Fix verification

| D-ID | Verdict | Measurement |
|---|---|---|
| D-R22-01..07 | Confirmed | PCB `5516eeec…` at both `ec8cb98` and `c70d261`. fit_check, plate_model and masses.json are untouched. fit OK: 5.003 / 2.98 / 0.89 mm. |
| R22-MECHANICS-01 (records) | Confirmed | C410 2.004, C420 2.004, R102 1.998, C431 2.051 mm. |
| D-R21-05 | Confirmed | Poses as recorded. Strain at 100 g: R81 1039, C87 1006 microstrain. |
| D-R21-01 | Confirmed | No mechanical change. |
| D-R19-07 | Confirmed | C84: no F.Paste on either land. |
| D-R19-14 | Confirmed | J440 margin 2.98 mm, wire room 5.00 mm. |
| Plate record | Confirmed | Modes 180.8 / 255.6 / 287.8 / 407.0 Hz. Mass 78.6 g. Gaps 0.261 / 0.320 mm. |

## Fix now

All four. None changes the board:
- 01: text.
- 02: sled and text.
- 03: text, bench and firmware rule.
- 04: text.

## Closed

- **In-plane shear at 37 g:** C84 1.1 N (its pads are 6.5 mm apart along the axis), J122 3.7 N, J3 0.36 N. This is P3 staking.
- **Random vibration** (GEVS 0.16 g²/Hz analogy, Miles, Q 10–20): 3σ deflection at C431 is 0.66–0.94 mm against its 1.30 mm gap, over about 540 cycles per burn.
- **Nylon supports:** about 43 N each at 280 g is acceptable. PA66 creeps near 70 °C (advice).
- **J3, L400, L1:** no finding.

## Comparison with round 22

Round 22's mechanics lens (read after these findings were written) had none of these four. Its one Minor was the keep-off list, which is now fixed.

## Coverage limits

- No physical harness, sled, chute or thermal test was done.
- Vehicle mass, Cd, crush distance and the board-to-air thermal resistance are Inference.
- The NASA workmanship page could not be reached; the 3 × OD figure rests on a vendor FAQ.
- The sled is modelled as rigid.
