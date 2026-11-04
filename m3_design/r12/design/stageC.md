# R12 stage C: copper (2026-11-04) — IN PROGRESS, not complete (updated after D-R12-29 … -32)

Stage C of `r12_plan.md` §4. **Status: the copper infrastructure is written and the plane / island scheme is fixed,
but the board is not routed.** The drafting router's best run on the stage B placement (`9881aaa3…`) leaves 36
unconnected items, a few clearance faults of its own and 78 route_check findings, so no copper table is frozen:
`m3_design/r12_routes.tsv` does not exist, `r12_build.sh` stops after stage B, and `m3_design/r12/m3.kicad_pcb` is the
placed board with no copper. Decisions D-R12-22, -23, -26, -27 and -28 are in `R12_DECISIONS.md`.

## 1. Infrastructure

| File | What it does |
|---|---|
| `m3_design/r12_route.py` (build) | Replays `m3_design/r12_routes.tsv` (every track and via, checked octilinear / non-zero, widths from one set, the one 0.45 / 0.3 mm via, no via twice), draws the planes of `m3_design/r12_planes.tsv`, a B.Cu GND pour (minimum width 0.5 mm, so no pour sliver or finger can form) and the S-8 keep-outs round J121's barrels on In1 / In2, then fills the zones. No search. |
| `m3_design/r12_planes.tsv` (build input) | In1 one GND plane; In2 the 3V3 plane with three islands at priority 1: RAW_PROTECTED under the aft power cells, 3V3A under the IMU / baro, PORT_4V8 under the forward GH row (D-R12-22). |
| `m3_design/r12_aid/` (drafting aid, not run by the build, D-R12-26) | `export.py` (KiCad Python: the placed board's pads, rule areas and holes to JSON); `astar.c` (octilinear A* on F / B with through vias: 45-degree turns only, middle segments ≥ 0.5 mm and end segments longer than max(width, 0.2 mm), so no right angle, acute angle, short segment or tiny jog by construction; a per-path via budget); `route.py` (exact clearance fields from pad polygons, track capsules and via discs at 0.1 mm nodes; rip-up support); `plan.py` (the plan: widths, the U9 necks, the U1 fan-out, plane / island fan-outs, partner GND vias, rip-up and reroute, and the TSV writer). Needs numpy and a C compiler. Its output is reviewed and frozen into `m3_design/r12_routes.tsv`; the build replays only the table. |
| `m3_design/r12_build.sh` | Stage A, stage B (fit_check, placed DRC, check_r12 placement), and — once `r12_routes.tsv` exists — stage C (replay, DRC with parity and zero unconnected, fit_check, route_check r12, check_r12 copper). |

## 2. Design rules the aid enforces (all from the gate, D-R12-03 / -23)

Copper clearance 0.1 mm; test pads 1.0 mm; Tag-Connect pads 0.508 mm; copper to the board edge 0.5 mm; NPTH 0.2 mm;
a via centre ≥ 0.35 mm from foreign copper (hole 0.15 + JLC's 0.2 mm via-hole-to-track, D-R12-23), ≥ 0.30 mm from any
pad (V-2), ≥ 0.6 mm from any other via, ≥ 0.83 mm from a plated pad hole (the 0.55 mm inner PTH rule); a critical net
without a pour uses at most two vias (route_check extra_vias: every R12 pad is on F, so it needs none); a plane-net via
lands inside its own In2 island (0.5 mm in) and a 3V3 via 0.6 mm clear of every island; the fire path (BAT_IN,
ACT_FET_S, RAW_ACT, PYRO1_IGN, PYRO1_OUT) stays on F.Cu with no via; widths BAT_IN 1.0, RAW_ACT / ACT_FET_S /
PYRO1_* 0.8, RAW_PROTECTED 0.8, VLOGIC 0.5, CAM_5V 0.6, VBUS / PORT_4V8 0.5, switch nodes 0.8, signals 0.1 at U1 and 0.2
elsewhere, each limited to 0.8 × the smaller pad dimension at its ends (IPC-2152 sizing not yet checked: stage D).

## 3. Fixed copper (drawn before any search)

* **U1 fan-out (D-R12-27).** Ring-1 signal balls: a 0.1 mm F.Cu stub straight out 0.8 mm past the outer row; ring-2
  signal balls: diagonally to the channel between two ring-1 balls (one channel per stub, assigned) and straight out
  the same distance; every other used ball (rings 3–5, and every GND / 3V3 / VCAP ball) a dog-bone to a free
  interstitial via site next to it (0.566 mm from four balls: 0.141 mm copper and 0.216 mm hole clearance, legal under
  D-R12-23). 39 stubs, 43 dog-bone sites. F.Cu inside the ball field carries only these; B.Cu under it only the
  dog-bone nets. A 1 mm corridor past each stub end is kept clear of other nets.
* **U9 necks.** BAT_IN enters pin 5's 0.3 mm bar through a 0.3 mm neck from (14.9, 15.1) (the 1.0 mm trunk ends
  there; the narrow part runs straight into the pad within 1 mm, route_check neck rule); RAW_PROTECTED leaves pin 6's
  bar straight into C82.1.
* **J3 pin pairs.** DP (B6 / A6) and DM (A7 / B7) interleave at 0.5 mm, so each pair is linked on B.Cu through two
  vias just west of the pads (staggered at x 38.0 / 37.4), VBUS (B4A9 / A4B9) through two vias at x 36.6.
* **Same-part links on F:** LPS28DFW pad 7 → pad 5 (D-R12-25), U4 GND 2–3 and 6–7, J9 GND 3–4, U2 VIN 4–5, J9 CAM_5V
  1–2.

## 4. Draft result (latest run, 2026-11-03/04, not frozen)

On the placement with the owner's connector changes (D-R12-29 J121 DB125 terminal, D-R12-30 J1 5.0 mm pads, D-R12-31
SH 1.0 ports) and the IMU moved aft (D-R12-32), with three rip-up passes:
- **Search:** 24 connections left unrouted (28 unconnected items after DRC).
- **DRC:** no clearance or hole violation remains; only dangling copper from the unfinished nets.
- **route_check r12:** about 90 findings. 43 are dead_copper and 6 dangling_via from the unfinished nets. The rest are
  16 staircase, 4 track_loop, 4 fold_back, 3 extra_vias, 3 detour, 3 acute_angle, 2 collinear_overlap and 6 single
  others.
- The best runs over the session sit between 21 and 31 unrouted connections; the count no longer falls with rip-up alone.

Unrouted at the last run, by area:
- QSPI into U3: CLK, IO2, NCS.
- IMU MOSI.
- SD: CS, MISO, MOSI.
- Port UARTs at the series resistors: AUX, radio.
- Servo 2–4: at D121, R156 and R157.
- Pyro control: ACT_EN_MCU, PYRO1_CONT (R129).
- NRST at J2; BOOT0; CAM_5V_SENSE; CAM_MCU_RX / TX; LED_YEL; PORT_SENSE; VCAP2; VLOGIC_SENSE; I2C1_SDA at U5;
  BAT_FAULT_N at U9.4.
- Fan-outs: C21 (3V3A), C24 and R401 (GND), R400 (PORT_4V8).
- USB_DP partner GND via.

Is the TFBGA routable? The ball fan-out itself completes every time: 39 stubs and 43 dog-bones, every dog-bone net
leaves the field on B.Cu, and no unrouted connection is a U1 escape. The failures are F.Cu congestion round U3, J430,
the IMU and the resistor rows. So there is no evidence that the package needs changing (R12_DECISIONS D-R12-02 stands).

## 5. What stage C still needs

1. Raise the router's completion: per-area placement fixes round U3 (rotate or give its south row a free side), the
   IMU (move the east-side pins' neighbours), J3 / VBUS, D121; longer rip-up chains; a second pass over the failures.
2. Fix the aid's two DRC defects (minimum spacing between a path's own vias; the PTH-hole via rule at J3's shell).
3. A clean-up pass for route_check: re-route each connection with a higher turn cost to remove staircases, jogs and
   local bumps; add partner GND vias where the 1.5 mm rule still fails.
4. Freeze `m3_design/r12_routes.tsv`, run `r12_build.sh` to DRC 0 / unconnected 0 / parity 0, fit_check r12, route_check
   r12 0 failing, check_r12 copper; then stage D.
