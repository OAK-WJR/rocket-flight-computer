# R12 stage C: copper (2026-11-04) — IN PROGRESS, not complete (updated after D-R12-34)

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

## 4. Draft result (latest runs, 2026-11-04, not frozen)

**Placement pass 2 (D-R12-33)** moved U3 (rotated, IO0 / CLK / IO3 toward U1), the servo series resistors (in line
with J122's pins, two staggered rows) and pull-downs (2 × 2 block beside D121), the port series resistors and 100 nF
(behind their SH pins, 1.0 mm pitch), the SD pull-ups (on their contacts' x), C10 / R164 (off U4's south band, 3V3A
island extended aft) and LED2 / R33 (aft-east). It passes stage B (fit_check, placed DRC 0 / parity 0, check_r12
placement). The aid now runs with turn cost 2 / via cost 8, a larger search budget, up to 8 rip-up passes, a
`--clean` pass and slot-aware plated-hole keep-outs (D-R12-33).

Runs on that placement (`PYTHONHASHSEED=0`; each about 15 min):

| Run | Passes / clean | Unrouted after search | DRC unconnected | DRC violations other than dangling | route_check failing (of which dead_copper + dangling_via) |
|---|---|---|---|---|---|
| p4 | 6 / no | 22 | 25 | 4 hole_clearance (J3 slot, fixed since) | 61 (28) |
| p5 (best) | 6 / yes (p4's report) | 11 | 17 | 4 hole_clearance (J3 slot, fixed since) | 55 (20) |
| p6 | 8 / yes (p5's report) | 17 | 23 | 0 | 78 (34) |

For comparison, the stage B placement's best draft: 24 unrouted, 28 unconnected, about 90 route_check findings.
p5's hygiene findings apart from the unfinished nets: 13 staircase, 6 detour, 5 extra_vias, 3 track_loop, 2 fold_back,
2 acute_angle and 6 single others. The `--clean` pass re-routes about two thirds of the flagged units with fewer bends
and keeps the old copper of the rest.

Unrouted in p5: QSPI_NCS (U3.1), SD_CS (R460), SD_MISO (R462), PYRO1_CONT (R129), ACT_EN_MCU (R122), CAM_5V_SENSE
(C94), SERVO3_MCU (R152), LED_YEL (R33), and three plane fan-outs (C21 3V3A, C24 and R401 GND). The set changes from run
to run (p6 left VLOGIC_SENSE, I2C1_SCL, GPS_TX / RADIO_RX at the port resistors and C97 / C22 instead): the rip-up
search is now congestion-bound in three areas, not placement-bound at one part:
- the band between the aft power cells and U1 (y 14–40), which every aft-side signal (servos, camera UART, sense
  dividers, pyro control) must cross to reach the west or south side of U1;
- U1's east side (QSPI, SD, USB, I2C to the baro, LED_YEL);
- the pyro cell's control nets (R122, R129) into U1's west column.

Is the TFBGA routable? The ball fan-out still completes in every run (39 stubs, 43 dog-bones), and no unrouted
connection is a U1 escape, so D-R12-02 stands (Inference: an incomplete search is not proof either way).

### 4.1 Three signal layers (D-R12-34)

In2 is now a mixed layer (3V3 pour and islands plus low / medium-speed signals; In1 one unbroken GND plane). The aid
routes F / B / In2 with through vias (`astar.c` takes up to three layers; `route.py` models In2's obstacles: islands,
U1's 3V3 core, S-8 reach of J121, plated-hole walls, and the fast-net reference rule; `plan.py` `in2_ok`, `fast`,
the long-slow-first order, the In2 preference and the 3V3A cluster's In2 tier). `export.py` now also exports footprint
rule areas (J2's Tag-Connect keep-out: earlier drafts put a 3V3 track in it, DRC items_not_allowed). C24 moved (stub
pocket). The S-8 rule areas forbid tracks and vias on In1 / In2.

Runs on the D-R12-34 placement (`PYTHONHASHSEED=0`, about 20–30 min each; scratch, not frozen):

| Run | Settings | Aid failures (unrouted units incl. fan-outs / partners) | DRC unconnected | route_check failing (dead_copper + dangling_via) |
|---|---|---|---|---|
| a3 | 6 passes, MAXEXP 4M, core 5.0 | 17 (14 + 3 partners) | 22 | 60 (23) |
| a4 | 8 passes, MAXEXP 8M, core 5.0 | 15 | 23 | 61 (25) |
| a5 | fast nets may use In2 (unpreferred) | 22 | — | — |
| a6 / a8 | core 4.5, blockers see a fan-out's end via | 16 / 20 | 23 / 27 | 51 / 56 |

The 3V3 pour is not yet guarded by the aid: in a2 it is one piece (40 of 40 3V3 vias in one fill outline; opened by
0.5 mm, a 1.0 mm neck, 37 of 40 stay joined, the other three local fan-outs), but in a4 In2 tracks cut off a 16.7 mm²
piece holding one 3V3 via (one of a4's DRC unconnected items; 35 of 40 vias in the 1.0 mm-neck piece). The aid needs a
3V3-connectivity term (or a post-pass that moves the offending In2 run) before a table is frozen. In2 carries 60–90 tracks per
draft (servos, port UARTs, BAT_FAULT_N, sense lines, LEDs, SWD), so its capacity is not the limit: the rip-up search
itself plateaus at 15–22 failures, and the failing set moves between runs. Persistent ones: the R401.2 GND fan-out
(boxed in by U400's FB network), the 3V3A H1 cluster (C21 / C22, 15 mm from its island), U3's QSPI_NCS / IO2, the
microSD resistors (SD_CS / MOSI / MISO), I2C1 to U5, NRST / SWCLK to J2, and one or two of the servo / port UARTs.

## 5. What stage C still needs

1. Finish the search: with three signal layers the limit is the rip-up search, not capacity. Next: a negotiated-
   congestion (PathFinder) cost in `astar.c` (a per-node history cost on each layer, every net re-routed each
   iteration with sharing allowed and penalised, until no node is shared), instead of rip-up. Local fixes the drafts
   point at: R401.2 GND (join it to C94.2 or move R401 so its GND pad faces a free via site), the 3V3A cluster (route
   C22.1 to the island over In2 as a normal 0.3 mm net, or give H1's 3V3A a small In2 island under C21 / C22), and the
   J2 / U3 / microSD pockets.
2. Run `--clean` on the completed draft until no staircase / detour / loop finding is left, then the partner-via pass,
   then hand fixes for singles.
3. Freeze `m3_design/r12_routes.tsv`, run `r12_build.sh` to DRC 0 / unconnected 0 / parity 0, fit_check r12, route_check
   r12 0 failing, check_r12 copper; then stage D.
