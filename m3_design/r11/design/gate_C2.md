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

## 4. D-R11-40: R11's own K-rules

Gate lane, `tools/` only. `check_r10.py` is unchanged, so R10's gate keeps R10's floors (R23-GATE-03) and its
condition-blind later-rule test. `fab_manifest.py` is untouched.

**What was wrong.** `check_r11` K-rules ran `check_r10.k_rules` with only the DRU hash swapped, and that hash was the
DRU's own (a self-pin). So R10's floors judged R11's board: 0.15 mm clearance and track, 0.5 / 0.3 mm via, 0.25 mm hole
to hole and 0.15 mm net-class clearance. That gave 13 findings. The 14th came from the later-rule test, which compared
layers only, so the via-only rule "R11 board floor: via hole to hole" (0.2 mm) looked as if it could override "JLC pad
hole to hole" (0.45 mm).

**What K-rules does now** (`check_r11.k_rules`):

* `m3.kicad_dru` is pinned by SHA-256 in `tools/check_r11.py` (`R11_DRU_SHA256`, now `b483f287…`). A reviewed DRU
  change re-pins it there. `r11_gate_data.json` cannot re-pin it.
* Every DRU minimum is read as KiCad reads it (`check_r10.dru_rules`). Each must be at least its `R11_DRU_FLOORS` entry.
  A constraint with no floor fails, and so does a severity other than error.
* `R11_JLC_TABLE` keeps R10's four JLC hole rows and adds six for R11's floor rules. Each row's rule must exist exactly
  once, with its pinned layer and condition and a minimum at least JLC's figure. The six new rows are: clearance
  0.09 mm, track 0.09 mm, via drill 0.15 mm, via diameter 0.25 mm, via hole to hole 0.2 mm and PTH annular ring 0.15 mm.
  R10's four rows include PTH pad hole to inner copper at 0.3 mm (R21-GATE-02).
* A later rule fails if it sets a pinned row's constraint below JLC's figure and can meet the pinned rule on both
  layer and condition. Two conditions "meet" unless their top-level `&&` terms of the form `A/B.Type` or
  `A/B.Pad_Type == '…'` contradict each other in both orders, (A, B) and (B, A), since KiCad tries a two-item rule
  both ways round. A `Pad_Type` term also requires `Type == 'Pad'`. A condition with a top-level `||`, or a term of
  any other form, contributes no fact, so the test can only err toward a failure.
* `.kicad_pro`: the design rules are held to `R11_PRO_FLOORS`. Every net class's clearance, track width, via diameter
  and via drill are held to `R11_NETCLASS_FLOORS`, and its via ring (diameter − drill) / 2 must be at least 0.05 mm.
  No severity may be set to ignore, and there may be no DRC exclusion.
* The board itself, unchanged from R10: `check_r10.pth_inner_copper` checks every PTH hole wall against JLC's 0.3 mm
  to foreign copper on In1 … In4. `check_r10.jlc_board_holes` checks the PTH ring (0.20 mm), via ring, plated hole
  size, NPTH size and ring, NPTH to copper, via hole to copper, PTH to outer copper and pad hole to hole.

**Floors and sources.** All figures are from JLCPCB's capability page, https://jlcpcb.com/capabilities/pcb-capabilities
(read 2026-11-03). The page gives multilayer figures, which cover the six-layer board; it has no six-layer column.
No floor is below JLC's figure.

| Floor | R11 floor | JLC figure (page section) |
|---|---|---|
| Copper clearance (DRU, .kicad_pro, net classes) | 0.1 mm (D-R11-15) | 0.09 mm: "Min. track width and spacing (1 oz)", multilayer (Traces) |
| Track width (DRU, .kicad_pro, net classes) | 0.1 mm (D-R11-15) | 0.09 mm (Traces). JLC's "3 mil acceptable in BGA fan-outs" is not used |
| Thermal gap and spoke, physical clearance, diff-pair gap | 0.1 mm | 0.09 mm (Traces) |
| Via diameter / via drill | 0.25 / 0.15 mm | "Min. via hole size / diameter", multilayer 0.15 / 0.25 mm (Drilling) |
| Plated hole (`min_through_hole_diameter`, DRU `hole_size`) | 0.15 mm | Multilayer drill 0.15–6.3 mm (Drilling) |
| Via ring (`min_via_annular_width`, DRU `annular_width`, net-class via) | 0.05 mm | Via diameter 0.1 mm over the hole (Drilling) |
| PTH annular ring (DRU rule) | 0.15 mm; the board is held to 0.20 mm | 1 oz multilayer: recommended 0.20 mm, absolute minimum 0.15 mm (Traces) |
| Hole clearance (`min_hole_clearance`, DRU `hole_clearance`, physical hole clearance) | 0.20 mm | "Via hole to track" and "Inner layer via hole to copper clearance", 0.2 mm (Traces) |
| PTH pad hole to inner copper | 0.30 mm (DRU 0.55 mm, D-R21-01) | "Inner layer PTH pad hole to copper clearance", 0.3 mm (Traces) |
| PTH hole to outer track | 0.28 mm | "PTH to track", min 0.28 mm, 0.35 mm recommended (Traces) |
| Hole to hole (`min_hole_to_hole`, via–via) | 0.20 mm | "Via hole-to-hole spacing", 0.2 mm (Drilling) |
| Pad hole to hole | 0.45 mm | "Pad hole-to-hole spacing", 0.45 mm (Drilling) |
| Microvia diameter / drill | 0.2 / 0.1 mm (R11 draws none; every via is held to 0.15 mm on the board) | "Min. drill diameter for 2- or more-layer PCBs is 0.1 mm" (Drilling) |
| Copper to edge | 0.5 mm (R10's) | ≥ 0.2 mm from routed edges (Outline) |
| NPTH size, ring, to track | 0.50, 0.45, 0.20 mm | Drilling and Traces rows, unchanged from R10 |
| Silkscreen text 1.0 / 0.15 mm, silk clearance 0.15 mm | REQUIREMENTS M2 | not JLC figures |

**Tests** (`tools/test_r11_check.py`, `R11KRules`, plus one `R11RealBoard` case):

* The committed DRU and `.kicad_pro` pass.
* A hash mismatch fails, even when the only change is a comment.
* A looser DRU fails: clearance 0.08 mm fails on the hash. Re-pinned to its own hash, it fails on the 0.1 mm floor and
  JLC's 0.09 mm. A via diameter of 0.2 mm also fails.
* A rule below the JLC floor fails: an added rule with hole to hole 0.15 mm, hole size 0.12 mm or track 0.09 mm.
  So do `.kicad_pro` values of `min_clearance` 0.08, `min_via_diameter` 0.2 or `min_hole_to_hole` 0.15, and a net
  class with via drill 0.1 mm or clearance 0.09 mm.
* The via–via condition rule is evaluated only for vias. `conditions_meet` holds pad–pad against via–via, `A.Type ==
  'Via'`, no condition, `'||'` and the swapped order. The project's DRU passes `jlc_table_r11`, while R10's
  condition-blind test still flags it. A later 0.2 mm hole-to-hole rule with no condition, `A.Type == 'Pad'` or a
  `||` condition fails. A via–via rule at 0.18 mm fails JLC's 0.2 mm.
* A PTH hole wall 0.2 mm from foreign In3 copper fails JLC's 0.3 mm; at 0.4 mm it passes.
* Real board (copy): K-rules is clean.

Measured on a copy of the C3 board in the worktree (2026-11-03): K-rules is OK. `pth_inner_copper` found no foreign
inner copper within its 1 mm reach of any PTH hole on that copy, since In1 / In4 are not poured yet. Its 0.3 mm rule
is exercised by the synthetic seed. Re-check it once the ground family pours.

## 5. K-loader: R11's own loader list

Gate lane, `tools/` only. `check_r10.py` and its `LOADER_R10` are unchanged (R10's gate is frozen).

**What was wrong.** `check_r11` K-loader ran `check_r10.loader_pins`, whose allowances are keyed to R10's pin map. On
R11's map (D-R11-41, D-R11-49) that gave 8 findings: PA15, PB10 and PB11 had no allowance, PB9's named I2C1_SDA, and
the PA2, PA3, PE11 and PE12 allowances were stale.

**What K-loader does now** (`check_r11.loader_pins_r11`, list `check_r11.LOADER_R11`):

* The loader-pin set is `check_r10.LOADER_H74X` unchanged (AN2606 Rev 70 Table 135, pp. 320-323 = Rev 64 Table 119,
  pp. 277-280). U1's balls come from `pin_table.tsv` (`port` → `r11_ball`). PF0 / PF1, PH13 / PH14 and PI0-PI3 have no
  ball on TFBGA-100.
* Each entry is keyed by port pin and carries the net the pin may carry, the net's other members (pad → part value;
  `None` only for USB_DM / USB_DP, R10's USB contract), the decision, the section of `stageC1b.md` holding its
  R17-MCU-02-form case, R10's AN2606 citation and the electrical reason.
* It fails on a loader ball that carries a net with no entry, an entry whose ball carries another net, members that
  differ from the entry, and an entry for an NC ball or a port with no ball (stale).
* It also fails on an entry for a port outside `LOADER_H74X`, a missing field, a citation other than R10's, a decision
  with no `## <id> ` heading in `R11_DECISIONS.md`, and a case section with no heading in `stageC1b.md`. An entry may
  name R10's case only while `LOADER_R10` has the same port, net and members.

**Entries** (members as on the worktree R11 board on 2026-11-03, which git does not track yet; Measured):

| Port (ball) | Net | Members | Decision | Case |
|---|---|---|---|---|
| PB9 (A4) | CAM_MCU_TX | U12.5 | D-R11-49 | stageC1b §8.4 |
| PA15 (A8) | SERVO2_MCU | R151.1, R155.1, D121.3 | D-R11-49 | stageC1b §8.4 |
| PB10 (J7) | I2C1_SCL | R12.1, U5.8 | D-R11-41 | stageC1b §7 |
| PB11 (K7) | I2C1_SDA | R13.1, U5.7 | D-R11-41 | stageC1b §7 |
| PA4 (G3) | LOGIC_SOURCE_ST | R91.2, U11.9 | D-R11-01 | R10's LOADER_R10 |
| PA5 (H3) | BAT_FAULT_N | R89.2, U9.4 | D-R11-01 | R10's LOADER_R10 |
| PA6 (J3) | VLOGIC_SENSE | R60.2, R61.1, C60.1 | D-R11-01 | R10's LOADER_R10 |
| PC10 (B9) | SD_SCK | J430.5 | D-R11-01 | R10's LOADER_R10 |
| PC11 (B8) | SD_MISO | J430.7, R462.1 | D-R11-01 | R10's LOADER_R10 |
| PC12 (C8) | SD_MOSI | J430.3, R461.1 | D-R11-01 | R10's LOADER_R10 |
| PA11 (C10) | USB_DM | not pinned | D-R11-01 | R10's LOADER_R10 |
| PA12 (B10) | USB_DP | not pinned | D-R11-01 | R10's LOADER_R10 |
| PB6 (B5) | QSPI_NCS | R10.1, U3.1 | D-R11-01 | R10's LOADER_R10 |

No entry for PA2, PA3, PE11, PE12 or PB15: they are NC on R11 (D-R11-49), so an entry would be stale.

**Tests** (`tools/test_r11_check.py`, Measured):

* The real map passes. LOADER_R11 is exactly the loader ports with a net in `pin_table.tsv`'s `r11_net`, and a board
  built from the entries gives no finding, directly and through `check_board`.
* A net on PA9 with no entry fails, as does dropping PA15's entry.
* PB9 carrying I2C1_SDA against its CAM_MCU_TX entry fails, and so does a new member on SERVO2_MCU.
* A PA2 entry on an NC ball is stale, and so is PB10's entry when its ball is NC.
* Provenance: an unknown decision, a missing case section, a different citation, a false R10 case, a non-loader
  port and an empty reason each fail.
* `R11RealBoard.test_k_loader_holds_on_the_real_board` runs when `R11_BOARD` is set. On a scratch copy of the
  worktree board, K-loader is OK (Measured).
