# R10 round 34 — parts lens

Target `c2a11fd`, board SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and after.

**Totals: 0 Critical / 0 Major / 0 Minor real errors.**

## Checks
- Board fields against both BOMs: all 207 BOM designators match the board's LCSC code, maker part, footprint and value;
  unlisted board items are TP pads and J2 (Tag-Connect, not fitted).
- CPL (206 rows) against board positions and sides: all match except the recorded J3 / J430 EasyEDA origin offsets.
- JLC's own `model` per LCSC code (`stock_check.json`) equals the BOM maker part on all 81 lines.
- Every R / C maker part decoded against its value, tolerance, voltage and dielectric: all agree.
- Capacitor voltage ratings against each cap's net: 16 V parts only on ≤ 5 V rails, the rest ≥ 25 V against 8.4 V.
- Datasheet facts in `parts_qualification.md` re-read from the cached PDFs (TPS25947, TPS2553, TPS7A91, TPS709, AP63201,
  AON7524, AONR21357, AO3400A, ESD103) and the derived figures recomputed (C123 τ, D402 EN shift, R92 bleed, LDO thermal,
  L400 ripple, camera ILIM, C126 discharge tail, R134 pulse margin, Q120 Vgs, R162 currents, U401 pad / vias): all reproduce.

## Fix verification
- R33-TRI-01 (U9 exposed pad, ORDERING 8.3): pads 5 / 6 and 9 exposure 0.15–0.25 mm measured on the board; text matches. Confirmed.

## Observations (5, not counted)
1. parts_qualification:655 cites TPS2553 "SLVS841F equation 1 (p15)"; rev G numbers it eq. 1 / 3 on pp16–17. Constants and result are right.
2. TPS25947 reverse-polarity note (≥ 350 kΩ on EN / OVLO pull-ups, bidirectional TVS): met.
3. U13 TPS709 EN open: allowed by the datasheet (internal pull-up).
4. TPS7A91 input and dropout headroom: inside limits.
5. U9 OVLO pin stays in its 0.5–1.5 V range above about 4.1 V pack.

Coverage limits: no live supplier fetch; CPL rotations rely on the gate's `jlc_orient --verify-cpl`; lands other than U9 / U401 not re-derived.
