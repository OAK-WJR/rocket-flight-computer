# R11 stage C5: K-reference, the ACT_DRV void under NRST and HSE_OUT (2026-11-03)

Follows stageC4.md section 6 (O-C4-2, first cause). Decision D-R11-60 in `R11_DECISIONS.md`. Nothing is committed or
ordered. Evidence labels as AGENTS §2.5. Coordinates are board mm (x east, y forward from the aft edge, KiCad's y). The
new sites were found by hand on the tables and a scratch plot; nothing searches in the build (D-R11-07).

## 1. The cause

The ACT_DRV barrel (15.40, 29.70) keeps a 1.3 mm rule area on In1..In4 (S-8: GND counts as foreign copper for the
P-FET gate drive). On In4 that is a void under:
* NRST's B.Cu run (18.05, 29.75) - (16.55, 29.75) - (14.75, 27.95), and
* HSE_OUT's B.Cu run into C26.1 (x 16.18, y 28.37 - 28.60): its west edge comes to 1.31 mm from the barrel, inside the
  keep-out's circumscribed 16-gon (1.325 mm at the vertices) (Calculation).

On the stage C4 board (`142ec65f…`) K-reference listed 869 samples: 621 of them in this void (618 NRST, 3 HSE_OUT) and
248 elsewhere (Measured; stageC4.md section 6 split them 624 / 245; the 14 NRST samples at (20.00 - 20.04, 27.55) F.Cu
and (21.56 - 21.64, 32.25) B.Cu are not in the void and belong to the 248).

## 2. Why both the barrel and NRST move

* NRST alone: NRST must cross ARM1_SENSE's In3 diagonal (19.50, 30.90) - (11.65, 23.05) on B.Cu and drop to In3 south
  of it. Its B.Cu path south is closed by the B.Cu runs leaving the ball field west (GND y 29.32, BAT_FAULT_N y 30.0,
  3V3A y 30.4, ARM1_SENSE y 30.8, 3V3 y 31.7), so the drop must lie between ARM1_SENSE's diagonal and the 3V3A run. The
  only F.Cu room there was ACT_EN's branch to Q122.1 (x 17.57), which moves (section 3). With the barrel kept, HSE_OUT's
  3 samples remain.
* Barrel alone: NRST's old route encloses the barrel on three sides (B.Cu y 29.75 north, In3 x 14.0 west, In3 y 32.0
  south); inside that loop no site is 1.375 mm from all three (the north-south gap is 2.25 mm; Calculation), and outside
  it ACT_DRV cannot reach R121.2 (B.Cu) past ACT_GATE's trunk (x 13.6) and the 3V3 / GND copper.

## 3. What moved (D-R11-60)

| Item | Before | After |
|---|---|---|
| ACT_DRV barrel (`r11_route_pyro.py` VD) | (15.40, 29.70) | (15.55, 29.95), same 0.4 / 0.2 mm via, same 1.3 mm keep-out |
| ACT_DRV F.Cu | Q122.3 - (16.6, 31.2) - (15.85, 31.2) - (15.4, 30.75) - barrel | ... (15.85, 31.2) - (15.55, 30.9) - barrel |
| ACT_DRV B.Cu | barrel - (15.07, 30.03) - R121.2 | barrel - (14.40, 29.95), inside R121.2, 0.08 mm off its centre |
| ACT_EN F.Cu to Q122.1 | (17.57, 28.4) - (17.57, 29.85) - (17.87, 30.15) - Q122.1 | (17.57, 28.4) - (18.50, 29.33) - Q122.1 |
| NRST B.Cu after C24.1 | ... (18.4, 28.95) - (18.4, 29.4) - (18.05, 29.75) - (16.55, 29.75) - via (14.75, 27.95) | (18.85, 28.5) - via (17.65, 29.70), one diagonal |
| NRST In3 | (14.75, 27.95) - (14.0, 28.7) - (14.0, 31.1) - (14.9, 32.0) - (19.4, 32.0) - (20.0, 32.6) | (17.65, 29.70) - (17.65, 31.20) - (18.45, 32.00) - (19.40, 32.00) - (20.00, 32.60) |

The barrel's site limits (Calculation on the tables, DRU floors 0.1 mm clearance and 0.25 mm hole clearance):

| Limit | Requirement | At (15.55, 29.95) |
|---|---|---|
| R164.1 (3V3, B.Cu pad top y 30.325) | via centre >= 0.35 mm (hole clearance) | 0.375 mm |
| C123.2 (GND, F.Cu pad east edge x 14.98) | >= 0.35 mm | 0.57 mm |
| G_Q122 GND via (14.73, 31.20), ring 0.225 mm | S-8: centre >= 1.425 mm | 1.495 mm |
| G_Q122B GND via (17.00, 29.30) | S-8: centre >= 1.425 mm | 1.59 mm |
| HSE_OUT's copper edge at C26.1 | outside the 16-gon: >= 1.33 mm | 1.46 mm |
| NRST (new) | outside the keep-out | via 2.11 mm, In3 x 17.65 2.1 mm |

NRST's via (17.65, 29.70), centre distances: ARM1_SENSE's In3 centre line 0.46 mm (copper gap 0.21 mm, hole edge to
its copper 0.31 mm); 3V3A's B.Cu run edge (y 30.25) 0.55 mm; Q122.1 / Q122.2 pad edges (F.Cu) 0.525 / 0.725 mm; GND via
(17.00, 29.30) 0.76 mm, which is its GND partner (AGENTS §3) (Calculation; DRC below is the measurement).

## 4. Results (Measured)

`m3_design/r11_build.sh` twice: stage A gate OK, fit_check r11 OK, every family's stage check OK up to `ground`, which
fails only on the three allowlist requests of stageC4.md section 4 (unchanged coordinates); DRC 0 violations,
0 unconnected. Both builds: SHA-256 `4e552ef4087b61c6e9c9d864b8be2bce5424fd08ed76d145f9cd5086d0980349`.

check_r11 (full) on a zone-filled copy with its fit report:

| Rule | Result |
|---|---|
| S-1 … S-9 (S-3c included), W-1, W-2, LC-1, M-1, M-3, M-5 … M-8 | OK |
| K-copper, K-inner, K-region, K-plane, K-fill, K-rules, K-lands, K-width, K-power, K-ports, K-loader | OK |
| K-legends | FAIL: stage D (unchanged) |
| K-reference | FAIL 1 finding, 248 samples: the plane antipad boundary samples only (stageC4.md section 6, gate lane) |

* K-reference: the 621 void samples are gone; the 248 left are the same sample set as on `142ec65f…` (set comparison:
  0 new, Measured).
* S-8 OK: 8 barrels, 24 inner rings. ACT_DRV's barrel to the nearest foreign inner copper 1.069 mm (In1 GND, G_Q122's
  ring; was 1.10 mm to In2 3V3A). Board minimum unchanged: 1.01 mm (ACT_GATE (14.60, 15.90) to BAT_FAULT_N on In1).
  PTH hole wall to foreign inner copper still 0.55 mm minimum.
* PYRO1_GATE / PYRO1_GATE_N to 3V3 / 3V3A: the same minimum as before on every layer (0.200 mm on F.Cu, PE4's lane to D2's land, D-R11-23; 0.386 mm is the C3 escape stub, corrected
  by D-R11-87; no gate-net or 3V3 copper changed).
* route_check `--profile r11`: 3 failing (SD_MOSI critical_via_no_gnd and extra_vias, CAM_RX_BUFFER extra_vias, same
  coordinates and figures), 0 allowlisted; non-critical leftovers 25 (was 27: NRST's tiny_jog (18.85, 28.5) and detour
  are gone); no new instance in any category, INFO included.
* r11_escape_check --board: OK (69 rows, 0 open). `r11_fanout.tsv` unchanged (NRST's exit, via (19.55, 27.60) west on
  B.Cu, is the same).

## 5. Open (not verified)

* O-C4-2's second cause (248 antipad boundary samples) stays with the gate lane.
* Signal integrity of NRST and HSE_OUT, JLC DFM and any electrical test: not run.

## 6. SD_MOSI's escape: three vias, no jog (D-R11-63)

Board `ad7b500`'s build (`4e552ef4…`) left one route_check finding: `extra_vias SD_MOSI` (4 vias, 1 + 2 allowed).
D-R11-61's 3-via counter-example needed a 0.2 mm F.Cu piece between U1's B8 / B9 and A9 / A10 balls (gated
`short_segment` and `tiny_jog`). Coordinates below are board mm; U1's balls are 0.4 mm pads on a 0.8 mm pitch (A9
(26.8, 24.4), A10 (27.6, 24.4), B8 (26.0, 25.2), B9 (26.8, 25.2), B10 (27.6, 25.2), C8 (26.0, 26.0)).

**Why the escape has to pass between SCK and MISO** (Calculation on the board's copper, then confirmed with DRC on scratch
copies):
* C8 can leave only by its north-east corner (C9, an NC pad, closes the C row; the B / C gap east is closed at USB_DM's
  corner (28.0, 25.6); the C / D gap by the GND via (27.2, 26.4)). From there it goes north through the B8 / B9 gap or the
  B9 / B10 gap.
* Through the B9 / B10 gap, SD_SCK (B9) would have no exit: its north-west corner is MISO's, its other three are on
  MOSI's path.
* SCK on a field via at B9's south-east corner (27.2, 25.6): B.Cu there is closed by QSPI_IO2 (y 24.4, then x 29.0);
  In3 by SD_CS's run (27.2, 27.2) - (28.95, 25.45) - x 28.95 to y 20.95 to the east and SERVO2_MCU (x 26.1) to the west;
  further north, K-region holds a 3V3-region run west of PORT_5V3 (x >= 29.4), and the B.Cu drop sites there lead into
  SD_MISO's loop, CAM_RX_BUFFER's x 29.45 run and J430's pads. The gate lane's grid router (scratch, clearances relaxed
  0.035 mm) found only a 2-via SCK route that wanders through the field on F.Cu, runs In3 to y 11 and B.Cu along y 11-12
  under J430 (Measured on the scratch board): rejected.
* So MOSI goes north through the B8 / B9 gap, east in the A / B row gap (one 0.1 mm track: the pads leave 0.4 mm), north
  between A9 and A10 (x 27.25: 0.1 mm to A10, and the hole clearance to SWCLK's via (26.8, 23.6)). Its first diagonal
  must keep 0.2 mm (centre lines) from MISO's diagonal, its chamfer 0.2 mm from SCK's, its A / B-gap run must be at least
  0.5 mm (tiny_jog) and its chamfer at least 0.2 mm long (short_segment). With MISO and SCK leaving from their ball
  centres the run can be at most 0.23 mm (Calculation). Starting each 0.0999 mm off its ball centre, inside the pad and
  under route_check's 0.1 mm `pad_end_offcentre` line, gives 0.5128 mm against 0.5 (an in-pad stub instead makes a
  gated `staircase`, Measured on a scratch copy).

**Copper** (D-R11-63):

| Net | Layer | Points |
|---|---|---|
| SD_MOSI | F.Cu | C8 (26.0, 26.0) - (26.35, 25.65) - (26.35, 24.9936) - (26.5836, 24.76) - (27.0964, 24.76) - (27.25, 24.6064) - via (27.25, 23.15) |
| SD_MOSI | B.Cu | (27.25, 23.15) - (28.60, 21.80) - (28.60, 18.25) - via (29.80, 17.05) (the rest of the net unchanged) |
| SD_SCK | F.Cu | (26.8707, 25.2707) - (27.3214, 24.82) - (27.83, 24.82) - via (29.50, 23.15) |
| SD_MISO | F.Cu | (25.9293, 25.1293) - (26.40, 24.6586) - (26.40, 23.40) - (27.90, 21.90) - via (29.45, 21.90) |
| GND | via | (28.25, 23.00), SD_MOSI (27.25, 23.15)'s partner, 1.01 mm |

Clearances at the narrow points (Calculation, centre-line spacing for 0.1 mm tracks, 0.2 mm needed): MOSI's first
diagonal to MISO's 0.2015 mm; MOSI's chamfer to SCK's diagonal 0.2015 mm; MOSI's A / B-gap run (y 24.76) to A9 0.11 mm and
to B9 0.19 mm (copper gaps); MOSI's turn (27.25, 24.6064) to SCK's corner (27.3214, 24.82) 0.225 mm; SCK's diagonal to
B10 0.216 mm and its A / B-gap run to A10 / B10 0.17 / 0.13 mm (copper gaps). DRC is the measurement: 0 violations.
B.Cu: MOSI's x 28.6 run keeps 0.275 mm from the 3V3 via (28.05, 19.22) and 0.30 mm from the SD_CS / SD_DAT2 vias at
x 29.15 (copper gaps).

**Results (Measured).** `m3_design/r11_build.sh` twice: every stage check OK, the final `ground` check OK (exit 0, 0
route_check failures), `r11_escape_check` OK (69 rows; F N exits 9, In3 N 6); SHA-256
`b7e2decb49bce5b24d124e24dd886d38a8e634ad7c2d203885f7125a6771bbb5` both times. On a zone-filled copy: DRC 0, unconnected
0; check_r11 every rule OK except K-legends (stage D), K-reference OK; S-8 minimum 1.01 mm, ACT_DRV 1.069 mm
(unchanged); PYRO1_GATE / _N to 3V3 / 3V3A minimum unchanged (0.200 mm, D-R11-23; was misquoted as 0.386 mm, D-R11-87). route_check `--profile r11`: 0
failing, 2 allowlisted, 0 stale, 0 out of date, 25 unrecorded non-critical leftovers; its full `--list` output differs
from `4e552ef4…`'s only by the removed `extra_vias SD_MOSI` instance (every category, INFO included). SD_MOSI 22.65 mm,
3 vias; SD_SCK 15.53 mm, SD_MISO 23.85 mm (lengths Measured). `tools/test_route_check.py` (85 tests) and
`tools/test_r11_check.py` (40 tests, R11_BOARD on the zone-filled copy) pass.

**Open (not verified).** The 0.0015 mm margins over the 0.1 mm clearance and the 0.0128 mm over route_check's 0.5 mm
jog line are drawing margins only (Calculation); JLC's DFM on the BGA escapes, signal integrity of the SD bus and any
electrical test are not run.
