# Round 33 mechanics review (claude)

Target commit `feed21f`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and after.

**Totals: 0 Critical / 0 Major / 0 Minor real errors.**

## Findings

None.

## Fix verification

- R32-TRI-01 (R166-to-C84 courtyard gap): 0.65 mm centreline, 0.60 mm outer edge, as recorded. Confirmed.
- R32-TRI-02 / -03: outside this lens.

## Observations (not counted)

- fit_check --profile r10 on a0ec075e: OK, 0 issues. J3 margin 0.886 mm (x -0.45, z 3.25); all eight DB125 bodies 2.976 mm; 27 tails minimum 7.558 mm, 2.20 mm below the board, 1.80 mm to a 4 mm sled; L1 B(25,74.6) 3.015825 mm below the bottom face (0.984175 mm to a 4 mm sled plane); J430 closed box 15.05 x 15.70 x 2.10 mm.
- Independent bore arithmetic: DB125 corner (42.6, 8.9) with 0.3 mm tolerances gives r 21.92 mm, 2.98 mm inside 24.9 mm; J3 corner (-0.45, 3.25) gives 24.014 mm, 0.886 mm.
- Supports: Edge.Cuts circles r 1.6 mm at (4,4), (42,4), (4,44.3), (3.7,86), (42,86), exactly the five recorded. Nearest bottom envelope C32.2 4.536 mm, nearest top exposed land LED2.2 (GND) 3.8079 mm from (4,44.3); LED1.1 3.860, J2.1 (3V3) 3.880, J2.3 (NRST) 3.987 mm (round lands: centre distance minus 0.3937 mm radius).
- Plate model re-run (tools/plate_model.py --profile r10, sources/r10_design/masses.json, this round's fit report): pinned D5 180.8 Hz, D10 255.6, clamped 287.8 / 407.0 Hz, 78.6 g, max 100 g deflection 1.27 mm at (46,44.5). 100 g D5 gaps at 4 mm: C431 0.2613, C421 0.3199, L1 0.524, C411 0.558 mm; onsets 125 / 133 / 175 / 214 g (D10 250 / 265 / 351 / 428 g); at 3.5 mm C431 and C421 overlap. All match ORDERING 8.4, M3_R10 and the handoff (the D10 / clamped / 1.24 mm figures are labelled to 632a9ad3, already ruled).
- Pocket window x 31.5-41, y 20-60 contains C411 (x 32.85-35.55, y 21-24.5), C421 (32.05-35.55, 35.4-38.1) and C431 (37.95-40.65, 56-59.5) model boxes.
- Hardware bounds: nut-inclusive h + t limits 6.018 mm at x 4 / 42 and 5.365 mm at x 3.7, recorded conservatively as < 6.0 / < 5.3 (already ruled in round 32). 4 mm + 1.0 mm and 4.5 mm + < 0.8 mm both meet them.
- Wire room: sqrt(25.4^2 - 5^2) - 19.6 - 0.3 = 5.003 mm for all eight terminals (fit_check 5.003-5.603); 4.493 mm at 24.9 mm; 5.32 / 4.82 mm at 3 mm height; bend arithmetic 3.9 / 4.1 / 5.1 / 5.7-6.5 mm for 22 / 20 / 18 / 16 AWG reproduces.
- Compass (north = smaller y = aft, y forward, x east): DB125 -90 deg has its wire face at x 3.40 (west), +90 deg at x 42.60 (east), matching the handoff table. J440 forward body end y 23.45 (so y < 23.5 is aft of the body); J3 F(4.6,30.8) body y 26.33-35.27 lies between J440 and the (4,44.3) support, then J121 (55.85) and J400 (65.85) forward, so 'never forward along x = 0' and the battery-lead 'never aft along the west top side' lists are in the right order. D402 B(4.45,65.9) lies between J400's pins (y 64.1 / 67.6). J440 envelope 3.93 mm from the (4,4) support. East column 34 g; J9 / J122 body gap at x 42 is 6.73 mm.
- Pin legends: bottom J121 2:E1+, J400 2:SW, J440 2:GND / 3:TXO / 4:RXI, J410 / J420 2:GND and 3:TXO, J9 2:GND and 3:RXI, J122 2:S2 and 4:S4; the rest on top, as the handoff lists. The board's J121 pin-1 legend uses an ASCII hyphen ('1:E1-') where the docs print a Unicode minus; typography only.
- DB125 lands: every terminal pad is 1.30 mm drill, 1.90 mm round land, as the handoff states.

## Checks executed

- shasum -a 256 of the board before and after (both a0ec075e...)
- tools/fit_check.py --profile r10 --report into the probe directory (KiCad Python)
- tools/plate_model.py --profile r10 --mass-spec sources/r10_design/masses.json (NumPy venv) and a gap / onset script (defl.py) for D5 and D10
- pcbnew probes: footprint poses, courtyards, Fab bodies and wire-entry markers of the eight terminals (geo.py, crt.py); support holes on Edge.Cuts (holes.py); DB125 pad sizes and outline (pads.py); silkscreen pin legends (silk.py); R166 / C84 courtyards (r166.py)
- Hand arithmetic for bore margins, wire room, bend room, hardware h + t limits and washer gates

## Coverage limits

- No physical harness, sled, screwdriver or hinge test.
- Plate model is Calculation/Inference with allowance masses.
- Fit relies on the committed VRML model boxes and fit_check's envelope allocation; models not re-derived from maker drawings.
- VEHICLE.md stack not re-read beyond the records' figures.
