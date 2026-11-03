# Round 34 routing lens (claude)

Target commit `c2a11fd`; board SHA-256 `a0ec075e…` before and after (probe copy identical).

**Totals: 0 Critical / 0 Major / 0 Minor real errors.**

## Checks executed
- route_check `--profile r10` on a copy: 0 failing, 0 allowlisted, 0 stale, `right_angle` 0, 5 unrecorded noncritical leftovers (informational, AUD-10), 28 bump windows: OK. `--routes` table recomputed.
- kicad-cli 10.0.7 DRC on a copy: 0 unconnected; only library-path warnings (199 `lib_footprint_issues`), no copper violation.
- Independent pcbnew probes (`.supervisor/r34_routing/probe1–7.py`):
  - all 1059 segments on 45° multiples; no zero-length, arc or dangling end;
  - 39 two-end nodes below 135° (35 at 90°, 4 at 45°), all in same-net pads or vias that cover the inner corner, so there is no free 90° or acute bend;
  - all 25 return-required critical vias have a GND via within 1.5 mm (max 1.492 mm, PYRO1_GATE). In2 under them: 3V3 ×17, PORT_4V8 ×4, GND ×3, void ×1. `pad_layer_changes` finds only J440.3 / J440.4, each 1.500 mm from its GND via.
- Quoted figures confirmed:
  - J440 clamp runs 3.864 / 3.964 mm, centre to centre 3.157 / 3.194 mm, pad edge to pad edge 1.865 / 1.900 mm;
  - J440 partner vias 0.300 / 0.800 mm;
  - via sizes 304 / 4 / 1;
  - board counts 1059 segments, 309 vias (170 GND), 1866.794 mm;
  - PYRO1_CONT_MID diagonal 0.2005 / 0.386 mm, net 10.57 / 6.81 mm;
  - 25 required critical vias, 21 over In2 power rails, GND partners 0.77–1.43 mm on those 21;
  - the 23-row detour table (the r21 method).

## Findings
None.

## Observations (not counted)
- The BUZZ_G T sits 0.020 mm before its chamfer (already a round 24 observation).
- Six clean mid-segment T joints.
- The detour totals differ only by method (117 nets / 1236.8 mm with zero-length nets included, against the recorded 116 / 1236.6).
- J420 / J9 clamp distance 3.064 mm, quoted as part of "3.1–3.4 mm": correct rounding.
- PYRO1_OUT's via sits in the S-8 void inside In2 GND, which section 6 calls "over In2 GND": loose wording, not false.

## Fix verification
R33-TRI-01 (U9 exposed-pad text) is outside this lens and was not re-measured.

## Coverage limits
- IPC-2152 widths (check_r10 K-power) not re-derived.
- Rail-to-GND capacitor distances not re-measured.
- No physical evidence.
