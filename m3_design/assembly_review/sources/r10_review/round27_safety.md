# R10 round 27: safety lens

- **Target:** commit `816038c`, board SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`, checked
  before and after (unchanged). Read-only; probes in `.supervisor/r27_safety/`.
- **Totals (real errors only):** 0 Critical / 0 Major / 1 Minor. 23 observations (not counted).

## Finding

### R27-SAFETY-01 (doc, Minor): the 3V3 clamp respin option is labelled "H-9", which is the FMEA's gate-source capacitor

- **What is wrong.** The current I-5 dispositions give the 3V3 over-voltage clamp or crowbar the FMEA label H-9:
  - `docs/FMEA_REDUNDANCY.md` line 37 (I-5 (R10) row): "Respin options: a 3V3 over-voltage clamp or crowbar (H-9), …";
  - `docs/R10_VALIDATION.md` line 2406 (§1 (a) / (b)): "… a 3V3 over-voltage clamp or crowbar (the FMEA's optional H-9), …".
- **What it contradicts.**
  - The FMEA's hardware change list defines H-9 as "A 1 µF/50 V 0603 (`C15849`) from `GATE_SW` to the common-source node
    (not to ground). +1 part, rated 'consider'" (`docs/FMEA_REDUNDANCY.md` §4.2, line 385).
  - `docs/R2_VERIFICATION.md` line 108 records "H-9 gate-source capacitor on the load switch: Done (C120 2.2 µF)".
  - No H-item (H-1 … H-10) defines a 3V3 clamp. The label comes from a slip in the original I-5 row (line 111: "Optional
    H-9 (3.6 V clamp on 3V3, …)"), which already disagrees with §4.2.
- **Evidence on the board.** The part H-9 describes is fitted on `a0ec075e…`: C120 (1 µF) from ACT_GATE (C120.2,
  B(17.1,73.3)) to ACT_FET_S (C120.1, B(17.1,71.75)), the Q120 / Q121 gate-source capacitor that AGENTS §2.4 requires.
- **Impact.** The only hardware remedy the records offer for the I-5 class points the owner at a different part that is
  already fitted and recorded "Done". A reader who follows the reference can take the clamp for a one-0603 change, or for
  done. The clamp itself is defined and analysed nowhere in the FMEA change list. No board or procedure change follows.
- **Fix.** In FMEA line 37 and R10_VALIDATION line 2406 replace the H-9 label with "(not an FMEA change-list item: the
  original I-5 row calls a 3.6 V 3V3 clamp 'H-9', but §4.2's H-9 is the load-switch gate-source capacitor, fitted on R10
  as C120)". Annotate line 111's "Optional H-9" as a mislabel.

## Fix verification (D-R26)

| Change | Measured on `a0ec075e…` (independent pcbnew extraction, Calculation on native geometry) | Verdict |
|---|---|---|
| D-R26-01, safety parts | J440.3 / .4 (and pins 3 / 4 of J410, J420, J9) not flashed on In1 / In2; J440.1 / J9.1 keep In2 rings 0.2505 mm from 3V3, so I-5's text stands; S-6, S-8 pass; route_check r10 0 failing on a copy | confirmed |
| D-R26-02, PYRO1_OUT ≥ 1.040 mm from 3V3 / 3V3A | 3V3: F.Cu 1.0500 (J121.1 run to via (9.2,52.55)), B.Cu 1.0511 (R173.1–D120.3), In2 1.0612, In1 1.5754. 3V3A: B.Cu 1.04001 by KiCad shape-collision bisection (R164.2's rounded corner to the run; 1.0404 with my 1 µm inside polygons). Before figures 0.5135 / 0.5662 / 0.6200 reproduced on `92c3ad59…` | confirmed |
| D-R26-03, rule 8 corner | Budget equation re-solved: 5.7132 / 5.5576 / 5.5555 / 5.5085 V; binding note obligation 43 carries it; PA6 window top 5.27 V stays below the corrected VLOGIC corner | confirmed |
| D-R26-04, gate nets ≥ 1.0 mm; audit | 3V3 to PYRO1_GATE 1.0585 (R128.1), to PYRO1_GATE_N 1.0650 (R127.1) / 1.0808 (R126.1), F.Cu; 3V3A 1.1450 (C10.1, B.Cu) and 1.6000 (U1.3); inner: 2.7505 (In2 3V3 fill), 3.354 (In1). Whole-board audit against `3d8e845`'s board reproduced exactly: 7 rows without fills, 6 with; BUZZ_DRV / PYRO1_OUT 0.9635 → 0.7935 mm (R162.1–R173.1, B.Cu) | confirmed |

## Observations (not counted)

1. The fire-chain audit (18 nets against every net, four layers) reproduces every §1, owner-row and FMEA figure (OUT–GND
   0.1768 / 0.1800, R173.1–source via 0.5000, R173.1–R162.1 0.7935, R173.1–BUZZ_G 0.5100, CONT_MID 0.1750 / 0.2500,
   R173.2–D120.3 0.4154, ARM1_SENSE–U13.5 0.1500, RAW_ACT–GND 0.3162, EN pairs 0.200 / 0.330 / 0.500 / 0.5197 mm).
2. PYRO1_IGN–3V3 0.7359 mm (R134.1, via (15.7,61.6)) and RAW_ACT–3V3 0.8370 mm (R132.1, via (28.1,59.4)) put bus voltage
   onto 3V3 when PC1 is high. Both are I-5 members (owner row 1 says "include"), not enumerated, and drive no match current.
3. Other unenumerated I-5 members: In2 barrels 0.2505 mm inside the opposite fill (3V3 via (26.4,79.26) in RAW_PROTECTED;
   VLOGIC, CAM_5V and VBUS vias and the USB_LIMITED track in the 3V3 fill), U2.1–U2.2 0.400 mm and U9.4–U9.5 0.200 mm.
   The fill-to-fill gaps are 0.300 mm, as stated.
4. PE4's net is 1.369 mm from the IMU_INT1 track under U1, F.Cu: the QSPI_IO2 row's class, beyond the 1.2 mm band.
5. Per-layer views of the D-R26-04 audit add drops that change no net-pair minimum (3V3 / I2C1_SDA 1.168 → 0.802 mm on
   F.Cu at R13's moved via; inner BUZZ_DRV / GND barrels; new AUX / GND). The per-pair list is complete; none is pyro.
6. Pairs under 1.2 mm with fills: 775 by my extractor (744 flashed copper only) against D-R26-04's 711. The count depends
   on the method, and nothing depends on it.
7. §1's "least RAW_ACT-to-GND gap 0.316 mm" keeps the preceding sentence's pad / track / via scope; the GND fill is
   0.2505 mm.
8. Owner row 24's 0.5205 / 0.5008 mm against exact 0.5197 / 0.5000 mm: KiCad circle polygonization, under 1 µm.
9. ACT_DRV–ACT_EN (Q122.3–Q122.1, 1.044 mm) turns the bus on with J400 open (VGS about −6 V through R121 / R123).
   Row 2's class; per-flight step 2 screens it.
10. ACT_EN_MCU is 0.8266 mm from RAW_PROTECTED (via (24.3,66.0)) and 0.670 mm from USB_LIMITED. Either bridge enables
    Q122 whenever PC1 is not driven. Row 2 class; the cold screen's bus-live refusal applies.
11. BAT_IN–RAW_PROTECTED (U9.5–U9.6 0.200 mm; BAT_IN via barrel 0.2505 mm on In2) turns the board on with J400 open.
    This is round 25 safety observation 3; step 2 screens it.
12. EN–OVLO (U9.1–U9.2, 0.200 mm) gives 0.57 V with J400 open and trips OVLO with it closed: fail-safe.
13. BAT_SW_SOURCE's via and J400.1's ring sit 0.2505 mm from In2 RAW_PROTECTED / GND. Neither turns the board on or
    latches it: fail-safe.
14. AGENTS §2 holds on the board:
    - every gate network is complete (Q124 R126 / R128 / C126 and R127; Q120 / Q121 R121 / R119 ∥ R120 / C120; Q122
      R122 / R123 / C123);
    - RAW_ACT is reached only through Q121;
    - S-1 … S-9 pass on a copy.
15. AON7524 VGS(th) is 0.4–1.2 V, so the recorded 3.23 V gate-net and 1.19–1.98 V QSPI cases do fire.
16. The 4.74 V "worst-case" load-switch |VGS| uses a 6.0 V minimum loaded BAT_IN. At the four-stall 5.713 V the same
    formula gives about 4.60 V, still at the −4.5 V RDS(on) point.
17. F6's "no sensor … failure may block deployment" against F8 / rule 1's barometer requirement: F6 reads as a
    software-robustness clause, and AGENTS §2.1 requires the barometer.
18. The cold-screen readings reproduce: healthy 99.37 / 99.34 mV; open 146.23 / 0 mV; OUT–3V3 0.295 V; CONT_MID–RAW_ACT
    102.0 / 55.5 mV (open match) and about 139 / 76 mV (intact match), both out of band.
19. Rule 8's corner reproduced (5.7132 / 5.5576 / 5.5555 / 5.5085 V).
20. C10's envelope is 3.0166 mm from U5's union, so the coat selection stands.
21. M3_R10's "FT limit of VDD + 4 V" follows DS12110 Rev 8 Table 119, and PC14 is FT.
22. DRC on a copy: 0 clearance / short violations and 0 unconnected. route_check r10: 0 failing; the pyro items are
    information only.
23. No tracked text quotes a pre-fix coordinate as current.

## Checks executed

- Board SHA-256 before and after.
- Independent copper extraction (KiCad 10 pcbnew, read-only) with a NumPy distance engine, on `a0ec075e…` and
  `92c3ad59…`.
- Distance audits:
  - the fire-chain audit;
  - the whole-board all-pairs comparison, with and without fills, per pair and per layer;
  - element checks of every quoted figure;
  - inner-layer clearances;
  - KiCad shape-collision bisection of the key pairs (OUT–3V3A 1.04001, OUT–3V3 1.05000, gate nets–3V3 / 3V3A 1.05847,
    OUT–BUZZ_DRV 0.79350 mm).
- Gates on copies:
  - check_r10 S-1 … S-9 with the project files;
  - kicad-cli 10.0.7 DRC;
  - route_check r10.
- Datasheets (DS12110 Rev 8 Tables 119 / 159 and the pin table; AON7524; AONR21357; AO3400A; DS41326).
- Calculations (the cold screen, the rule 8 corner, the bridge cases, VGS).
- Document cross-checks (§1, owner rows 1 / 2 / 24 / 27, FMEA I-5, I-2 / H-2 and §4, AGENTS, M3_R10, ORDERING 8.3 /
  8.4, REQUIREMENTS F6 / F8, D-R26-01 … -04).

## Coverage limits

- There is no bench or firmware evidence. Pin- and rail-overstress consequences are Inference.
- DRC ran without the schematic, so parity was not checked.
- Unflashed layers are modelled as drill-radius barrels, and pad polygons sit up to 1 µm inside the true shape.
- The hot-plug, chatter, TCR and plate models were not re-run.
- Round 26 safety's report was not opened, but two keyword greps printed one line each from the round 25 / 26 safety
  JSONs.
