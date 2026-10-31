# Round 19 - mechanics (Claude)

Board SHA-256 before and after: `a3144b15...` (unchanged). Totals: 0 Critical, 0 Major, 2 Minor.

- **R19-MEC-01** (Minor, new): DB125 legends are not under the nominal bodies (all 25 top legends checked against the drawing T0-1 body outline), but the pin-1 end legends 1:BAT+, 1:E1-, 1:S1 and J410 4:RXI sit only 0.10-0.16 mm off the body, inside the maker's tolerance and the 0.42 mm latch, and five wire-side legends lie under their own wires once wired. Fix: optional 0.5 mm move; state that pin identity after wiring is a continuity check.
- **R19-MEC-02** (Minor, new): C84 hand-fit: L1.2, C7.2, C9.1, C9.2 pads sit 0.0 mm (XY) under its pads, R166 0.56 mm away; no heat limit or re-inspection stated. Fix: add to ORDERING 8.2.

Confirmed: IMU axis map (+X=-x, +Y=-y, +Z=-z, roll = -gyro_Y, lever x = -6.0), wire room 5.003 mm (conservative envelope; maker nominal ~5.80), bore fit, supports, nylon hardware text. Details and coverage limits in the JSON.
