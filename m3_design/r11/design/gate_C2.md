# R11 gate changes for stage C2 open items O-C2-5 and O-C2-6 (2026-11-02)

Gate lane, `tools/` only (D-R11-08). R10's gate, profile and data are unchanged; `tools/ipc2152.py` gains an optional
`th_mm` argument whose default keeps R7–R10's copper. Nothing is committed, ordered or drawn by these changes.

## 1. O-C2-5: parallel barrels and single-via taps

**check_r11 K-power stays strict.** It runs R10's `SINGLE_OPEN_TAPS` mapped to R11 by function
(`check_r11.single_open_taps_r11`). R11 keeps R10's netlist and refdes (D-R11-01). Only U1's pad names change, so a
`U1.<LQFP pin>` becomes `U1.<ball>` through `pin_table.tsv`: PA4 28 → G3, VCAP1 48 → F8, VCAP2 73 → E7 and BOOT0
94 → D5. A U1 pin with no ball is an error, so no tap is dropped. The taps still include Q120.4 / Q121.4 → R121.1 and
the GND pads R85.2, R7.2, R8.2 and U10.2. A tap that hangs on one via fails unless `single_open_exceptions` (empty)
has an exact entry for it. The fix is a second barrel.

**route_check r11 accepts a listed pair.** New optional key `parallel_vias` in `r11_gate_data.json`:

```json
"parallel_vias": [
  {"net": "ACT_GATE", "vias": [[x1, y1], [x2, y2]], "reason": "measured reason"}
]
```

* Coordinates are board mm (KiCad's y). `vias[0]` is the first barrel and `vias[1]` the second barrel beside it. Each
  must be a via of `net` within 0.02 mm of its named point.
* The second barrel is left out of the loop search (`track_loop`), the net's via count (`extra_vias`) and the
  needless-hop pairs, as R10's `PARALLEL_VIAS` (D-R19-09, D-R24-02) did. Every other via and loop still counts.
* Fails as `parallel_via` (gated): a barrel that is gone (a stale entry), an entry whose net has no copper (stale), and
  a barrel that is not redundant on its own. "Not redundant" means that with only that via removed, some pad of the net
  is cut off. Both barrels are tested, so two vias in series are not accepted.
* A missing file or key means an empty list. A malformed entry raises an error and fails the gate. A malformed entry is
  one that is not exactly `net` / `vias` / `reason`, has an empty reason, does not have two numeric centres, or names
  the same point twice.
* `route_check.py --gate-data FILE` reads a different file. By default it reads `m3_design/r11/design/r11_gate_data.json`.

## 2. O-C2-6: R11 power paths and narrow pin entries

**Paths** (`check_r11.POWER_PATHS_R11`) are R10's 14 paths by function, rebuilt on R11's topology. R10's coordinates,
bridges and per-layer restrictions are gone.

* U9 IN: J1.1 (plated wire pad) → C88.1 → U9.5, all on B.Cu, with **no via allowed** (`max` 0). R10's 1.0 / 0.5 mm IN via
  was the DB125's side change, which R11 does not have.
* VLOGIC trunk (U11 / C99 on B.Cu → U2 on F.Cu) now changes side, so it needs 2 vias (D-R19-09's rule for a supply feed).
* Dropped "through" parts, because R11's placement moves them off the path: C404 (U400 OUT), C8 (U2 OUT) and C421
  (J420 feed).
* The three GH port feeds are treated the same: at least 1 via each into In2 PORT_4V8. R10's second via on J440 was a
  drawing detail (D-R19-14).
* CAM_5V must reach both J9.1 and J9.2.
* Every path via must be at least 0.5 / 0.3 mm. R11's power via is 0.6 / 0.3 mm.

**Floors** are computed, not drawn. Each track on a path must be at least the IPC-2152 width (`tools/ipc2152.py`,
external / internal fit, 30 °C rise, no plane credit, rounded up to 0.01 mm) for the path's R10 design current. The
width is taken on the track's own layer with R11 copper (`CU_MM_R11`: 0.035 mm outer, 0.0152 mm inner, stageB.md §3).
The table below is a Calculation on Inference inputs:

| Current | Basis (R10 budget) | Outer floor | Inner floor |
|---|---|---|---|
| 2.9 A | U9 IN / OUT | 0.68 mm | 1.83 mm |
| 2.0 A | U2 OUT | 0.36 mm | 0.96 mm |
| 1.9 A | U401 IN / OUT, port feeds | 0.33 mm | 0.88 mm |
| 1.81 A | U400 OUT | 0.30 mm | 0.81 mm |
| 1.294 A | VLOGIC (C84, trunk) | 0.17 mm | 0.46 mm |
| 1.249 A | U402 IN, CAM_5V | 0.16 mm | 0.43 mm |

U401 EN has no design current and keeps R10's fixed 0.2 mm floor.

**Narrow pin entries** come from the new schema of `power_narrow` in `r11_gate_data.json`:

```json
"power_narrow": [
  {"net": "BAT_IN", "pad": "U9.5", "layer": "B.Cu", "width_mm": 0.3, "max_len_mm": 1.0, "reason": "measured reason"}
]
```

* An entry excuses one connected run of below-floor tracks on `layer` that touches pad `pad` of `net`. Every track in
  the run must be at least `width_mm` wide, and the run's total length must be at most `max_len_mm`.
* `max_len_mm` may not exceed 2.0 mm (R8-GATE-04's narrow-run limit, as K-width).
* A run that is longer or narrower than its entry allows fails. So does an unlisted run, and a run touching a different
  pad.
* An entry that excuses nothing is stale and fails. A malformed entry is an issue.
* A missing key means the strict floor applies everywhere.
* R10's old tuple form of `power_narrow` is not read for R11.

## 3. Tests (seeded faults)

`tools/test_route_check.py` R11SixLayer:

* A listed pair passes. The same pair unlisted fails as `track_loop` + `extra_vias`.
* A pair on another net does not cover this one.
* Stale entries fail: a moved barrel, a missing second barrel, and a net with no copper.
* Pairs in series fail as not parallel, whether the series via is named first or second.
* Schema errors and file loading are tested.
* R10 keeps its frozen list.

`tools/test_r11_check.py` R11Rules:

* Path terminals agree with the R11 schematic netlist's nets, and the currents are R10's.
* Computed floors: 0.68 mm on B.Cu and 1.83 mm on In2 at 2.9 A.
* Pin entries: a listed entry passes. Over its length cap, narrower than listed, unlisted, on another pad, stale or
  malformed, it fails.
* An In2 segment fails its inner floor, and a via on U9 IN fails.
* The U1 tap mapping, with a missing ball as an error.
* Single-via tap Q120.4 → R121.1:
  * One barrel fails K-power.
  * An exact exception passes and then goes stale.
  * A second barrel passes K-power, and passes route_check r11 only when the pair is listed.

Not run on R11 copper: the R11 board in the worktree had no tracks when these checks were written (the design lane was
rebuilding it). K-power and route_check r11 on the real rails wait for the design lane's entries.
