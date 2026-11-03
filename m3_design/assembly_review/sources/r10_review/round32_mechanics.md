# R10 round 32: mechanics lens

Target commit `3366287`, board `a0ec075e…` (SHA-256 identical before and after). Reviewer: Claude. Strict real-errors rule.

**Totals: 0 Critical / 0 Major / 0 Minor.** No real error found.

## What was checked

- SHA-256 of m3_design/assembly_review/m3.kicad_pcb before and after (a0ec075e...); HEAD 3366287
- tools/fit_check.py --profile r10 on the committed board (KiCad Python, read-only) -> .supervisor/r32_mechanics/fit.json: OK; 235 rows; J3 margin 0.886 mm; terminal bodies 2.976 mm; wire room 5.003-5.603 mm on all eight DB125; 27 tails, min bore margin 7.558359 mm, 2.20 mm projection; deepest bottom L1 z -4.615825; nearest bottom C32.2 4.536177 mm; nearest top LED2.2 3.807887 mm
- tools/plate_model.py --profile r10 --mass-spec sources/r10_design/masses.json (NumPy venv) -> .supervisor/r32_mechanics/plate.json: f1 180.8 / 255.6 / 287.8 / 407.0 Hz, 78.6 g, max 100 g deflection 1.27 mm at (46, 44.5)
- own gap script on the plate solution (.supervisor/r32_mechanics/gap.py): 100 g gaps at h = 4 mm C431 0.261, C421 0.320, L1 0.524, C411 0.558 mm; contact loads D5 (D10) C431 125 (250), C421 133 (265), C411 175 (351), L1 214 (428) g; at h = 3.5 mm C431 -0.239, C421 -0.180 mm; at 4.5 mm first contact 173 g (C431)
- pcbnew dumps: outline 0..46 x 0..90; five Edge.Cuts support circles R 1.6 at (4,4), (42,4), (4,44.3), (3.7,86), (42,86); every terminal centre / rotation / pin net vs the handoff table; J430 B(24,24.3); L1 B(25,74.6); D402 B(4.45,65.9); J3 west overhang 0.44988 mm; footprint wire entry +y mapped to west (rot -90) / east (rot 90)
- pad-polygon distances to every support centre on F.Cu / B.Cu: LED2.2 GND 3.8079, LED1.1 GND 3.8601, J2.1 3V3 3.8799, J2.3 NRST 3.9870, C32.2 4.5362 mm
- pin-legend silkscreen sides vs handoff list (J121 2:E1+, J400 2:SW, J440 2-4, J410 / J420 / J9 2-3, J122 2 and 4 on the bottom)
- arithmetic: wire room sqrt(25.4^2-5^2)-19.6-0.3 = 5.003; with R 24.9 4.493; at 3 mm wire height 5.32 / 4.82; bend room 3.9 / 4.1 / 5.1 / 5.7-6.5 mm; body margin 2.976; washer edge 0.31-0.49 mm; J9-J122 body gap 6.73 mm; east column 34 g; retention worksheet forces; landing 98-163 g, 92 g, 367 g; stack joint + 79.4-83.4 mm and 32 mm margin; J440 forward body end 23.45; MEMS cover U5 outline + 1 mm clears U4 by 1.4 mm
- courtyard extents vs the short edges (M-8 queries) and J440-J3 courtyard distance

## Plate model

Re-run on `a0ec075e…` (fit report from this round's fit_check, `masses.json`): 180.8 / 255.6 Hz pinned D5 / D10, 287.8 / 407.0 Hz clamped, 78.6 g; 100 g gaps at 4 mm standoffs C431 0.261, C421 0.320, L1 0.524, C411 0.558 mm; contact loads 125 / 133 / 175 / 214 g (D5) and 250 / 265 / 351 / 428 g (D10). Every recorded figure reproduces.

## Fix verification

- R30-TRI-01 / R30-TRI-02 (round 30 fix pass): Electrical / thermal text corrections outside the mechanics lens — **not applicable to this lens**
- R29-TRI-03 (D-R29 docs: R10_VALIDATION section 8 terminal tails): fit_check on a0ec075e: terminal_tails.count 27, minimum bore margin 7.5583594 mm, 2.20 mm projection, 1.80 mm to a 4 mm plane; R10_VALIDATION line 3015 now says all 27 tails of the eight terminals and 7.558359 mm, the 'not re-run' sentence is gone — **confirmed**

## Observations (not counted)

- Plate model (D5 pinned, h = 4 mm) also puts J122.5's tail allocation onto the sled at 210 g (D10 419 g), outside the x 31.5-41 / y 20-60 relief pocket and before L1 (214 g); ORDERING 8.4's contact list does not claim to be complete and 210 g exceeds the 98-163 g landing range, so nothing stated is false.
- J9.1-.4 and J420.1-.4 tail allocations contact at 162-205 g (D5), inside the relief pocket (known from round 25; restated only as a reproduction).
- ORDERING 8.4 h + t bounds are conservative: stacking nut (2.4 mm) and 0.4 mm screw projection at the 3.175 mm corner radius with both 0.3 mm centring terms gives exact limits 6.018 mm at x 4 / 42 and 5.365 mm at x 3.7 against the stated < 6.0 / < 5.3 mm; the plate-only bound reproduces as 6.882 mm (stated 6.88).
- The records' 'not re-run on 1407e850 / 92c3ad59 / a0ec075e' plate provenance remains (round 29 observation); my re-run on a0ec075e reproduces every recorded figure.
- R16-MEC-01 B.Cu crossings under U4's body reproduce within 0.001 mm sampling: IMU_CS 0.852 (0.7596 + 0.0918), SPI1_MISO 0.325, IMU_INT1 0.325, 3V3A 0.33 mm; no via or B.Cu fill inside the body.
- R10_VALIDATION section 8's J440-to-J3 courtyard figure 1.67 mm reproduces (1.675 mm edge to edge including the 0.05 mm courtyard line; 1.730 mm centre lines).
- M-8's six recorded short-edge DFM queries reproduce: R400 / R401 / R404 1.025 mm, C403 1.955 mm (aft), C95 1.505 mm, R166 1.755 mm (forward).

## Coverage limits

- CAD envelopes and the optional plate model only; no physical hardware, harness, screwdriver, sled or vibration evidence exists
- Maker drawings (DORABO T0-1, Molex 472192001, TE MS5611) not re-read this round; envelopes taken from the bound VRML models and the records
- Wire-entry direction taken from the footprint descriptor ('wire entry +y') and the model box, not re-derived from the VRML geometry
