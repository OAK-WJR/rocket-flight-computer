# R10 round 33 — parts lens (Claude)

Target `feed21f`, board `a0ec075e…` (SHA-256 the same before and after the review).

**Totals: 0 Critical / 0 Major / 0 Minor real errors.**

## Checks
- **Board against BOM and CPL.** All 216 footprints were compared with the JLC BOM, the owner BOM and the CPL. The LCSC code, maker part, footprint, value and side all agree.
  - There are 81 BOM lines and 206 placed parts, with 45 Extended codes.
  - The only refs missing from the CPL are C84 (hand-fit), J2 and the test points.
- **CPL orientation.** `jlc_orient --verify-cpl` (read-only) rebuilt 67 top and 125 bottom rows with no error, plus 14 placement-only rows.
- **MPN decode.** Every MPN agrees with its Comment for value, voltage, dielectric and tolerance. This includes the UNI-ROYAL sub-ohm codes: 220K = 2.2 Ω (R164) and 360L = 0.36 Ω (R166).
- **Ratings against operating points.** Every capacitor's voltage rating is above its net's worst case (the SMBJ12CA clamp is 19.9 V). The TPS709 EN pin may be left open (300 nA internal pull-up). Diode, FET and protection pinouts are correct.
- **Datasheet facts.** The cached datasheets confirm the facts in `parts_qualification.md` for AONR21357, AON7524, AO3400A, SMBJ12CA, CRM2512, NX3225GA, MLT-5020, the LEDs and SRP5030T-6R8M.
- **Recalculation.** About 30 figures in `parts_qualification.md` were recalculated, all reproducing: the gate and RC time constants, the FET, R134 and U401 power and thermal figures, the rail tolerances, the fault currents, pack sag, C84 and the DB125 hole allowance.

## Fix verification
- **R32-TRI-03: confirmed.** The 85 °C part lists now read "among them …" in M3_R10, R10_VALIDATION, STATUS and `parts_qualification`. The X5R count is exactly 16 against the BOM, and the temperature ratings match the datasheets.

## Observations (not counted)
1. STM32H743VIT6 (rated −40…+85 °C ambient) is not named in the hot-end list. The list now says "among them", so it does not claim to be complete.
2. The J3 and J430 CPL rows carry deliberate EasyEDA origin offsets, and verify-cpl passes them.
3. Value fields mix two styles ("10k" / "10k 1%") on the same code. Cosmetic only.

Details: `round33_parts.json`.
