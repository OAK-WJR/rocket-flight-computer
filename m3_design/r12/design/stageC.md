# R12 stage C: copper (2026-11-05) — pass 1 FROZEN on the ported check_r12 rules (D-R12-72A); pass 2 (routing hygiene) open

**Update (D-R12-67A … -72A, 2026-11-05):** after `m3-assy-r12`'s ported check_r12 rules were merged, the D-R12-66A
table failed check_r12 copper (101 findings); the copper was reworked (§4.7) and re-frozen: board `c24fcf8272de3466f357a236f6cc4b2f455686a4685495b2cdc118bfef411a53`, DRC 0 /
0 unconnected / parity 0, check_r12 copper with every fatal rule at 0 (K-region 30, K-reference 1, K-plane 2 reported,
not fatal in pass 1), route_check r12 89 failing. The paragraph below describes D-R12-66A.

Stage C of `r12_plan.md` §4. **Status: pass 1 is done** (owner, 2026-11-04: "relax the cleanliness guidelines to get
it working first, then get routing nice in subsequent passes"). On the D-R12-61A … -64A pin map (placed board
`3b4f64da…`) the copper table `m3_design/r12_routes.tsv` is frozen; `r12_build.sh` replays it and builds board
`da48bb99031f30d7a79c4a985b83898543d62011ee13092409aca7f8cf395600` twice with the same hash: KiCad DRC 0 violations,
0 unconnected, parity 0; fit_check r12 and check_r12 copper pass; route_check r12 reports **83 failing** hygiene findings,
which pass 1 allows and pass 2 must clear (§4.6, §5). Decisions D-R12-22 … -54, attempt A's D-R12-55A … -60A and pass
1's D-R12-61A … -66A are in `R12_DECISIONS.md`. `m3_design/r12/m3.kicad_pcb` stays untracked (built, not committed).

## 1. Infrastructure

| File | What it does |
|---|---|
| `m3_design/r12_route.py` (build) | Replays `m3_design/r12_routes.tsv` (every track and via, checked octilinear / non-zero, widths from one set, the one 0.45 / 0.3 mm via, no via twice), draws the planes of `m3_design/r12_planes.tsv`, a B.Cu GND pour (minimum width 0.5 mm, so no pour sliver or finger can form) and the S-8 keep-outs round J121's barrels on In1 / In2, then fills the zones. No search. |
| `m3_design/r12_planes.tsv` (build input) | In1 one GND plane; In2 the 3V3 plane with three islands at priority 1: RAW_PROTECTED under the aft power cells, 3V3A under the IMU / baro, PORT_4V8 under the forward GH row (D-R12-22). |
| `m3_design/r12_aid/` (drafting aid, not run by the build, D-R12-26) | `export.py` (KiCad Python: the placed board's pads, rule areas and holes to JSON); `astar.c` (octilinear A* on F / B with through vias: 45-degree turns only, middle segments ≥ 0.5 mm and end segments longer than max(width, 0.2 mm), so no right angle, acute angle, short segment or tiny jog by construction; a per-path via budget); `route.py` (exact clearance fields from pad polygons, track capsules and via discs at 0.1 mm nodes; rip-up support); `plan.py` (the plan: widths, the U9 necks, the U1 fan-out, plane / island fan-outs, partner GND vias, rip-up and reroute, and the TSV writer). Since D-R12-35 / -36 it also negotiates congestion (`plan.py --pf N`: per-node present and history costs in `astar.c`, every unit re-routed each iteration, `--save-state` / `--load-state`) and guards the In2 3V3 pour (`Plan.pour3v3`, `label4()`). Needs numpy and a C compiler. Its output is reviewed and frozen into `m3_design/r12_routes.tsv`; the build replays only the table. |
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
* **J3 pin pairs.** DP (B6 / A6) and DM (A7 / B7) interleave at 0.5 mm: DP is linked on B.Cu through two vias just
  west of the pads (x 38.0), DM on F.Cu round those vias (to x 37.4 and back, D-R12-40), VBUS (B4A9 / A4B9) through two
  vias at x 36.6.
* **U1 B lanes (D-R12-43).** The 13 signal dog-bones leave on fixed B.Cu lanes to 0.8 mm past the outer ball row.
* **Hand copper (D-R12-41, -46, -55A, -56A).** `r12_aid/hand_fixed.tsv`: PYRO1_OUT; 3V3A complete (island fan-outs;
  the MS5607 and C32 joined to R164.2's via on F.Cu, D-R12-55A; H1 -> C22.1 -> C21.1 on F, a via west of C21 and an In2
  feed along x 13.0 / y 38.0 into the island's north edge, D-R12-56A).
* **Seed copper (D-R12-47).** `r12_aid/hand_seed.tsv`: stub-tip vias for SERVO3_MCU, SERVO4_MCU and LED_YEL (their
  nets are still searched).
* **Same-part links on F:** MS5607 GND 3 → 4 (D-R12-52), U6 die pad → 7 / 14 and VCC 15 → 16 → 1, 16 → C33.1
  (D-R12-57A), U4 GND 2–3 and 6–7, J9 GND 3–4, U2 VIN 4–5, J9 CAM_5V 1–2.

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

### 4.2 Negotiated congestion and the pour guard (D-R12-35 … D-R12-38)

The rip-up search is replaced by negotiated congestion (`plan.py --pf N`, D-R12-35) with a 3V3 pour guard (D-R12-36),
the R401 / C94 GND link and the cluster fan-out order (D-R12-37) and stub-tip vias at U1 (D-R12-38). An iteration
takes 20–60 s, so 40–100 iterations fit in 20–40 min. Runs on the D-R12-34 placement (`PYTHONHASHSEED=0`; scratch,
not frozen; "conflicts" are pairs of routed units breaking a clearance / via / reference rule, `route.conflicts`):

| Runs | Settings (beyond HW 1.6, MAXEXP 4M) | Best PF iteration | After the hard finish | DRC unconnected (other DRC) | route_check failing |
|---|---|---|---|---|---|
| p5 | pres ×1.6 to 15, every unit every iteration | 19 conflicts, 1 fail | (no finish) | 5 (16 crossings) | 76 |
| v1 … v4 | pres to 100–200, incremental after 10, In2 core 0.05–5 mm | 8–14 conflicts | — | — | — |
| x1 / x2 / x3 | + tip vias; core 0.05 / 5.0 / 0.05 (turn 3) | 18 / 11 / 16 (score) | 7 / 12 / 3 fails, 10 / 1 / 24 isolated 3V3 vias | 15 / 18 / 11 | 76 / 80 / 84 |
| y1 / y2 / y3 | turn 3, core 4.2 / 4.5 / 4.2, finish 8 passes | 22–24 conflicts | 16 / 12 / 11 fails, 7 / 9 / 13 isolated | 26 / 20 / 21 | — / 75 / 80 |

What this shows:
- The negotiation removes about 95 % of the sharing (≈ 300 → 8–20 conflicts) and keeps the 3V3 pour whole (0 isolated
  vias at most best iterations), but it does not reach zero: it oscillates among 10–25 units.
- The residue is local: U1's west side (x 14–20, y 35–48: the H1 3V3A cluster's run to its island past the crystal,
  SERVO3 / SERVO4, CAM_5V_SENSE, NRST, the C24 GND fan-out), the dog-bone escapes on B under U1 (VCAP2, QSPI_*, SD_*),
  the I2C / SD resistors north-east of U1 and the long PORT_4V8 cluster run.
- Opening In2 under U1 (core < 4.5 mm) adds capacity but cuts the supply-ball dog-bones out of the pour (10–24 isolated
  3V3 vias after the finish); the core must stay at about 5 mm.
- The hard finish (old rip-up on the few conflicting units) does not close the gap and ignores the pour guard; it should
  be replaced by more negotiation or local placement changes.

### 4.3 U1 forward, fixed B lanes, hand copper (D-R12-39 … D-R12-45)

The U1 cluster moved 10 mm forward into the empty forward band (D-R12-44; stage B passes: `r12_build.sh` stage A / B,
placed DRC 0 / parity 0, fit_check r12, check_r12 placement, placed board `72b47aee…`). The aid gained fixed B.Cu lanes
for U1's 13 signal dog-bones (D-R12-43), the J3 DM link on F and the start / goal fix that had left USB_DP / USB_DM
unrouted in every earlier draft (D-R12-40), hand-drawn PYRO1_OUT (D-R12-41, `r12_aid/hand_fixed.tsv`), partner-aware vias
(D-R12-42), an adaptive first window and a focus mode for the negotiation (D-R12-39), and pour repair plus
`r12_aid/prune.py` (D-R12-45). Runs on this placement (`PYTHONHASHSEED=0`, `R12_HW=1.6 R12_MAXEXP=4000000
R12_PF_FULL=10`, 4 in parallel, 45–60 min each; scratch, not frozen):

| Run | Settings | Best PF score | After finish | Best draft after clean + partners + prune: DRC (unconnected) | route_check failing |
|---|---|---|---|---|---|
| a1 / a2 | old aid, turn 3 / 2, cap 200 / 100 | 18 | 11 / 13 fails | 19 / 18 unconnected | 77 / 61 (pruned) |
| c1 | + window 1.5, USB / hand fixes | 16 | 10 fails | 14 (pruned) | 35 (pruned) |
| f1 … f4 | + B lanes; turn 2–2.5, window 1.5–3, cap 30–50, f2 focus | 13 / 18 / **8** / 26 | f3: 3 fails | f3 → cl1: 9 unconnected; → h1: **7 unconnected** | 40 / 44 |

cl1 (f3's finish, pour repaired, `--clean` with turn 2.5, partners, `prune.py --loops`): 0 clearance violations, 9
unconnected items, route_check 40 (14 staircase, 5 tiny_jog, 5 local_bump, 3 chain_detour, 3 extra_vias, 3 dead_copper,
2 critical_via_no_gnd, singles). h1 (cl1, then a greedy hard re-route of the failures: `R12_HW=3`, 15 M expansions,
20 rip-ups; partners; prune) joined the PORT_4V8 cluster and the R154.2 / R156.2 GND pair and leaves **7 unconnected**:
SD_SCK (J430.5 – U1.B9), LED_YEL (U1.B7 – R33.1), SERVO3_MCU (R152.1 – U1.H2), RADIO_TX_MCU (R451.1 – U1.J8), the 3V3A
cluster (C21.1 – C22.1: its B run ends 0.22 mm off the island via at (28.5, 29.9), DRC track_not_centered_on_via × 2) and
two dead GND fan-outs at (13.8, 49.0) and (21.0, 17.9); route_check 44. The 3V3 pour is whole in the aid's model except
one fan-out via at (25.5, 28.1). Hard-mode re-routes of the four signal nets stop at the A* expansion limit: their U1
stub tips (or, for SERVO3, R152.1 in the servo pocket) are walled in by neighbours' copper. The drafts are in scratch
only (not reproducible from the repository without the run settings above).

What the drafts show:
- Moving U1 forward cleared its flanks; the residue now sits at U1's stub tips (adjacent tips 0.4–0.8 mm apart cannot
  all take a via, so the last nets in cannot reach their tip) and in the aft power pocket (the servo network R150–R157 /
  D121, whose four nets cross each other between the series resistors, the pull-down block and D121; the PORT_4V8
  cluster at L400 / R400).
- The negotiation removes all but 8–20 conflicts and then oscillates whatever the settings; the hard finish turns those
  into 3–13 failures.

### 4.4 3V3A feed, seed vias, finishing attempts (D-R12-46 … D-R12-48)

Runs on the D-R12-44 placement with the 3V3A hand feed and seed vias (`--pf 60`, `R12_HW=1.6 R12_MAXEXP=4000000
R12_PF_FULL=10 R12_PF_PMAX=50 R12_PF_HIST=0.6`; scratch `r12c7`, not frozen):

| Run | Seeds / settings | Best PF conflicts | After finish, clean, partners, prune: DRC unconnected | route_check failing |
|---|---|---|---|---|
| v1 | S3 / S4; turn 2.5, window 1.5 | 15 | 13 | 49 |
| v2 | + LED_YEL; turn 2.5, window 1.5 | 7 | 14 | 27 |
| v3 | S3 / S4; turn 2.0, window 1.5 | 12 | 22 (no clean) | 41 |
| v4 | + LED_YEL; turn 2.0, window 2.5 (the repository's aid inputs now) | 9 | 10 | 64 |

None beats the h1 lineage. Finishing by search does not converge: a hard re-route of v4's leftovers with rip-up
(up to 25 units per connection) gave 12-32 unconnected, and a local negotiation (units within 2 mm of the failing
connections, the rest frozen, 40 iterations) stalled at 18+ conflicts and gave 16. Each leftover's shortest path against
the fixed copper crosses 10-18 routed units (LED_YEL: CC1 / CC2, I2C1, IMU_INT1, SD_MISO, SERVO2, VBUS, VBUS_SENSE,
VLOGIC; RADIO_TX_MCU: the GPS / radio UARTs, I2C1, NRST, SD_MISO / SD_MOSI; SERVO3_MCU: 18 units west of U1).

Best draft, h1 lineage (scratch `r12c7/h5`: `st.pkl`, `raw.tsv`, `ev/routes.tsv` pruned): h1, then the H1 cluster
re-routed with the In2 tier first and the two dead GND fan-outs re-done (h2: 5 unconnected, route_check 41), then
SD_SCK routed with the partner block off and a four-via budget (h5). **4 unconnected**: the 3V3A C21.1-C22.1 link
(SERVO4_MCU's F.Cu run at y 57.4 passes between C22 and C21), LED_YEL (R33.1), SERVO3_MCU (R152.1), RADIO_TX_MCU
(R451.1); one dangling GND via at (27.8, 52.6); route_check 47 (15 staircase, 9 local_bump, 7 tiny_jog, 4 extra_vias,
3 chain_detour, 2 critical_via_no_gnd (QSPI_NCS), singles). Moving CAM_MCU_RX's B escape one diagonal aft (s = 73.6)
frees LED_YEL's tip via at (24.6, 49.6), but LED_YEL then still finds no path to R33.1.

### 4.5 Routing attempt A on the Economic-sensor placement (D-R12-55A … -58A)

Placed board `ec461057…` (`r12_build.sh` stage A / B: r12_sch_check, fit_check r12, placed DRC 0 / parity 0,
check_r12 placement). Aid inputs: D-R12-55A / -56A hand copper, D-R12-57A U6 links, D-R12-47 seeds (D-R12-59A's PORT_4V8 seed came after
these runs). Scratch `r12ra`,
`PYTHONHASHSEED=0`, not frozen:

| Run | What | DRC unconnected | route_check failing |
|---|---|---|---|
| q2 / q6 | h5 (§4.4) ported: its fixed copper replaced by the new setup's, units breaking the new lands dropped, the changed-area nets re-routed (`R12_HW=3`, 8 M expansions, via budget 3) | 16 (q2) | 51 (q2) |
| pfA | `--pf 60`, HW 1.6, 4 M, full 10, pmax 50, hist 0.6, turn 2.0, window 2.5; finish | 19 | 41 |
| pfB | the same with turn 2.5, window 1.5; finish | 15 (the 3V3 pour split: 17 isolated vias) | 45 |
| hB3 | pfB, pour repaired (In2 culprits re-routed off In2), then a greedy hill-climb: each failing unit re-routed with 0 / 8 / 20 rip-ups (at most 12 units), kept only when failures + isolated 3V3 vias drop; partner block off, via budget 3 | **12** | 91 |

| o9 | hB3 + D-R12-59A's PORT_4V8 feed, LED_YEL / SWDIO re-routed alone, two GND stubs and two 0.2 mm tip-via pairs redrawn by hand, `prune.py --loops` | **7**, no violation | 71 |

o9's leftovers: SERVO2_MCU, QSPI_NCS, QSPI_IO2, SD_MISO, VBUS_SENSE, CAM_MCU_TX, HG_CS; route_check: 31 staircase,
12 local_bump, 11 tiny_jog, 8 extra_vias, 2 chain_detour, 2 critical_via_no_gnd and singles. Each leftover's path against the fixed copper alone crosses 4-17 routed units (QSPI_IO2 12, CAM_MCU_TX 14,
SD_CS / SD_MISO 9-17). The search has plateaued at 10-15 signal leftovers on every placement since D-R12-44.

Findings for the next pass:
- **SPI1 needs one more via than route_check allows** (D-R12-58A (a)): U6's west-face order and U4's north-face order
  are the same rotation, so at most one SPI1 net can join U6 and U4 on one layer; one net needs three vias (an
  extra_vias allowlist entry with that reason, or U6 rotated / moved so its SPI pins mirror U4's).
- **PORT_4V8** needs a hand-drawn F / B feed from C406 / L400 / R400 (y 20) to the forward island (y 88.4); an In2 run
  would split the 3V3 pour into east and west halves.
- route_check's local_bump candidates applied mechanically (scratch `bump.py`) fix only about a third: the others make
  right angles at their ends.

### 4.6 Pass 1: U1 re-pins and the frozen table (D-R12-61A … -66A)

D-R12-60A had shown that re-routing alone stalls at 6 unconnected because U1's aft rows and east column carried nets
whose pads lie elsewhere. Nine nets moved to free balls on the side facing their pads (D-R12-61A … -64A, `r12_sch.py`
`R12_MOVES`): QSPI_NCS PB6 → PB10 (J7); the barometer I2C to I2C3 on PA8 / PC9 (D9 / E9); the microSD to SPI4 on PE12 /
PE13 / PE14 (J6 / K6 / G7) with SD_CS on PA7 (K3); HG_CS PA10 → PC11 (B8); VBUS_SENSE PC8 → PA10 (D10). The schematic,
netlist and pin table are generated from that table; stage A / B pass (placed board `3b4f64da…`).

Runs (scratch `r12ra/ps/`, `PYTHONHASHSEED=0`; the trial tools `trial.py`, `seg.py`, `lneg.py` are scratch only):

| Run | What | Result |
|---|---|---|
| s1-s5 | single / grouped re-pins re-routed on BEST6 (D-R12-60A's draft) without a fresh search | 1-10 failing: the old copper was laid for the old map |
| pBa / pBb | full `--pf 60` (turn 2.0 / window 2.5; turn 2.5 / window 1.5), VBUS_SENSE on PC10 (B9) | 12-21 conflicts at iteration ~40 (stopped) |
| pCa / pCb | the same, VBUS_SENSE on PA10 (D10) | 3 conflicts; after the finish pCa 4 DRC unconnected, no violation |
| sw1 | pCa, DRC-judged blocker swaps (`swap.py`) | 2 unconnected: IMU_INT1, QSPI_IO2 |
| pDa / pDb / pCc, lnA-lnD | IMU_INT1 on PB6 (B5); turn 2.2; local negotiations of 10-26 units | 4-18 failing; not used |
| e19 | sw1 + D-R12-65A (QSPI_IO2 by a dog-bone and free B escape; IMU_INT1 without a B lane, routed from U4.4 through a via at (24.9, 30.6); SERVO2_MCU west of the IMU through (19.5, 40.0)) | **0 unconnected, DRC clean**: frozen |

The frozen table: 1423 tracks, 436 vias. route_check r12: 28 staircase, 13 local_bump, 9 tiny_jog, 8
critical_via_no_gnd, 6 extra_vias, 5 detour, 3 acute_angle, 3 side_by_side_overlap, 2 fold_back, and one each of
short_segment, collinear_overlap, crossing_without_node, right_angle, chain_detour and track_loop (83). QSPI_IO2 has six
vias (pass 1 allowed a third). The fire path is F.Cu with no via; S-8 keep-outs and the U4 / U5 rule areas pass DRC;
no foreign F.Cu track enters U6's pad ring.

### 4.7 Pass 1 on the ported copper rules (D-R12-67A … -72A)

The merge of `m3-assy-r12` brought check_r12's ported S- / W- / LC- / M- / K- rules; on the D-R12-66A copper they
found S-8 47, S-9 8, M-7 2, K-inner 10, K-region 32, K-reference 1, K-plane 1. Pass 1 now has two tiers (D-R12-67A):
the build passes `check_r12 --advisory K-reference,K-region,K-plane` until `R12_ROUTE_HYGIENE=strict`; S-, M-, W-, LC-
and every other rule stay fatal and cannot be named advisory. The copper changes, all drafted in scratch `r12ra/ps2`
(hand edits with `edit.py`, single-net aid searches with `seg3.py`: `seg.py` plus S-8 discs round the S-8 vias and a
no-via box on U6's body; KiCad DRC and check_r12 judged every step, `ev2.sh`):

| Rule | Change | Decision |
|---|---|---|
| S-8 | `r12_route.py` fill voids (r 1.35 mm, In2; In1 too for GND-hazard nets) round every S-8-net via; J121 keep-outs on In1 + In2, r 2.05 mm | D-R12-68A |
| S-8 | PYRO1_GATE_N (PE4) leaves U1 on F.Cu with no via (`hand_fixed.tsv`, `plan.py` `NO_ESCAPE`) | D-R12-68A |
| S-8 | ACT_EN_MCU tip via kept; HSE_OUT all F.Cu, SERVO3 / PYRO1_CONT / C24.2 GND vias moved; ACT_EN_MCU aft via to (16.4, 28.2); CAM_5V_SENSE / VLOGIC_SENSE re-routed | D-R12-68A |
| K-inner | IMU_CS joined on F.Cu; HG_CS F / B under U6; SPI1_MISO's U4 branch on B under U6 (no loop round U6); QSPI_IO2 off In2 | D-R12-69A |
| S-9 | BAT_IN J1.1 -> C80.1 -> TP80 -> Q120.3 at 1.0 mm; ACT_FET_S loop removed, ACT_GATE re-run at R119 | D-R12-70A |
| M-7 | U6 pin 1 -> C33.1 outside the pad ring; U6.13's via off the body | D-R12-71A |

Result (D-R12-72A): 1389 tracks, 430 vias; board `c24fcf8272de3466f357a236f6cc4b2f455686a4685495b2cdc118bfef411a53` twice; DRC 0 / 0 / 0; check_r12 copper fatal rules 0;
K-region 30, K-reference 1 (5283 loose samples), K-plane 2; route_check r12 89 failing. The aid does not yet model
S-8 or U6's body (O-R12-24); pass 2 must add both before any re-search.

## 5. What stage C still needs

0. **Pass 2 (next, after D-R12-72A):** add S-8 and U6's body to the aid (O-R12-24); clear route_check r12 (89 failing on
   `c24fcf8272de3466f357a236f6cc4b2f455686a4685495b2cdc118bfef411a53`); cut SPI1_MISO (four vias) and QSPI_IO2 (eight) back (QSPI_IO2 can take C3's freed B lane); bring
   check_r12 K-region (30), K-reference (1) and K-plane (2: 3V3 vias at (16.7, 48.8) and (18.1, 30.6)) to 0, then set
   `R12_ROUTE_HYGIENE=strict`. The D-R12-66A text follows.
0. **Pass 2 (as written for D-R12-66A):** clear route_check r12 (83 failing on `da48bb99…`): `plan.py --clean` with the build's
   route.json, then hand fixes; cut QSPI_IO2 to at most two vias besides its dog-bone (it now goes round U1's west and
   north sides: a B lane for A3 or a shorter F / In2 run east of U1); add GND partner vias at the eight critical layer
   changes; then set `R12_ROUTE_HYGIENE=strict` as the build default and re-run stage D. Items 0-4 below are history.

0. **Pass 1 (D-R12-60A):** blocker swaps reach 6 unconnected (CAM_MCU_TX, HG_CS, QSPI_IO2, QSPI_NCS, SERVO2_MCU,
   VBUS_SENSE); the U1 A-row / column-10 fan-out must change to finish.
0. **Attempt A (D-R12-58A):** the hand finish was not reached; the leftovers above, then the hygiene clean (about 90
   findings on the best draft), the freeze and the build checks remain.
0. **Status of the items below (D-R12-46 … -48):** item 1 was dropped (the band is the U1-north fan-out corridor);
   item 2 was done as fixed tip vias (`hand_seed.tsv`); item 3 was done (`hand_fixed.tsv`); item 4 was run (§4.4) and
   does not finish. What is left is the hand route of the four leftovers of h5, each of which needs 10-18 routed units
   moved, then the hygiene clean, the freeze and the build checks.
1. **Servo pocket (placement):** move the pull-downs R154–R157 and D121 out of the aft pocket into the open band the
   servo nets cross on their way (y 38–47), so each servo net is a plain line U1 → clamp / pull-down → series R → J122.
   (Inference: D121 behind the 1 kΩ series resistors protects the MCU pins as well near U1 as near J122.)
2. **U1 stub tips:** stagger the fan-out (alternate stub lengths, 0.8 / 1.5 mm past the outer row) so adjacent tips
   can both take a via, or make the slow west / north nets' tip vias fixed copper (they need no partner).
3. **3V3A at H1:** H1's decoupling link to C21 / C22 runs west across the stub corridor that SERVO3 / SERVO4 and the
   west-side nets use; take H1 to its caps through a tip via and B, or give 3V3A a fixed In2 feed from C21 / C22 to the
   island (`hand_fixed.tsv`).
4. Then re-run (`--pf 60`, f3's settings), finish, `fix` the leftovers, `--clean`, partners, `prune.py --loops`, hand
   rows for the last few, freeze `m3_design/r12_routes.tsv`, run `r12_build.sh` to DRC 0 / unconnected 0 / parity 0,
   fit_check r12, route_check r12 0 failing, check_r12 copper, and confirm the pour with KiCad's fill.

## 6. Older plan (kept for the record)

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
