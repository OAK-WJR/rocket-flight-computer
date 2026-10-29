# R10 circuit pass hand-over

Supervisor Steers 1–2 stop this pass after a reproducible, connected, DRC-clean
circuit commit. The separate layout agent owns the AVA pass and all subsequent
review rounds. This record does not award a clean review round.

Board at hand-over: SHA-256 `6e73b6ebe7e25d7a8c810493887fbaa7cce34f6fe1d379828dc67017e14235aa`
(46 × 90 mm, 209 footprints / 887 segments / 303 vias). Two complete
`m3_design/r10_build.sh` runs are byte-identical and pass the full `tools/check.sh`;
the 2304-case hot-plug model passes (simulation / Inference); the fab package is
regenerated and bound (live JLC 2026-10-29: $82.59 vs $84.41; R430 / U4 short).
Placement and routing reasons: R10_DECISIONS D-CIR-03; gate fixes: D-CIR-04.

Current source contracts are `sources/r10_design/circuit.json` and the reviewed
`pin_table.tsv` r10_net column. `parts.json` is a retired worksheet. The new
all-terminal, always-on-port, hinged-SD and audit-2 decisions are in
`sources/r10_design/R10_DECISIONS.md`. AGENTS §2 is unchanged.

| Entry point | Responsibility |
|---|---|
| `m3_design/r10_sch.py`, `r10_sch_check.py` | Native sheets/netlist, exact topology, ERC, seeds and board binding evidence. |
| `m3_design/r10_parts.py` | Maker-derived local lands/models and electrical budget; use KiCad Python, then `--check`. |
| `m3_design/r10_place.tsv`, `r10_pcb.py` | Every pose, 46 × 90 mm outline, five supports, no servo tie holes. |
| `m3_design/r10_route_core.py` | Translated MCU/QSPI/HSE/IMU/barometer geometry. U4 remains bottom/180°, roll=−gyro_Y, lever −6 mm. |
| `m3_design/r10_route_usb.py` | USB/SWD/NRST and the source corridor shared with the new SPI3 escape. |
| `m3_design/r10_route_pyro.py` | Single-switch load/fire topology, two direct filtered ADCs, source bridges and S-8. |
| `m3_design/r10_route_power.py` | Battery feed before C88/U9, damper, converters and In2 reference/supply regions. |
| `m3_design/r10_route_signals.py`, `r10_route_sd.py` | Direct GPS/radio UARTs, retained camera, servo/status/buzzer and SPI3. |
| `m3_design/r10_route_ground.py`, `r10_fanout.tsv` | Outer GND pours, explicit rail/ground fanouts and stitches. The aid freezes candidates; production generation never searches. |
| `m3_design/r10_post.py` | Individual terminal pin legends, sole SWD table, references and filled final board. |
| `m3_design/r10_build.sh`, `r10_fab.sh`, `tools/check.sh` | Deterministic rebuild, actual-feed hot-plug model, full CAD/software gates and board-bound fabrication package. |

Constraints that remain binding: maker pin/land/field identity; no hand editing
production boards; fast interfaces' ground partners within 1.5 mm and continuous
references; S-8 inner isolation at pyro barrels; only U401's two local-frame VIPPO
vias may enter a soldered SMD pad; real DRC/J2/TP clearances; five supports and bore
fit; current-limit/thermal and no-back-feed operating bounds. Audit 2 makes the
plate model optional, removes noncritical per-instance leftover paperwork and
uses the selected J-Tek's 1.125 A current floor; it does not waive those constraints.

Constraints that bit in this pass:
- **K-reference vs pin pitch:** a via's In1 void is r 0.40 mm and U1's pitch is 0.5 mm,
  so vias dropped on parallel adjacent lanes always leave a neighbour's edge
  unreferenced. Fan leaders out on 45° steps and keep every via ≥ 0.6 mm from
  foreign critical centrelines (the SPI3 fan from pins 78–81 does this).
- **West bundle:** SWDIO y 36.1, SWCLK y 36.6, NRST's single via (14.2, 37.3)
  (D-R2-09: exactly one transition on that leg), the four SD vias and
  USB_FAULT_N on B.Cu y 41.2 share the strip between J2 and U1's west pins.
- **USB corridor** (x 16–22, y 26–34) is boxed by VBUS_SENSE, USB_LIMITED and
  USB_DM; the SD lanes own B.Cu there, so USB_LIMITED crosses on an F.Cu overpass
  (two vias) and BUZZ_DRV uses a hop pair over it.
- **J420 is parked on the west edge** (5, 16): its radio lanes cross the USB / SD
  corridor; R451 sits on B.Cu at the forced hop to stay inside route_check's
  per-net extra-vias limit. Moving J420 east needs the camera cell moved, since
  J410 plus a second 4-position DB125 does not fit the east edge as placed.
- `r10_fanout.tsv` carries hand edits; rerunning `r10_fanout_aid.py` drops them.
- Four pour-only keep-outs `R8_POUR_TRIM_C1`–`C4` (in `r10_route_ground.py`) trim
  unfillable slivers; route_check recognises the prefix. Recheck them after moves.
- Any move of the J1 / C88 / U9 / R166 feed must pass the actual-feed hot-plug
  model again (it runs inside `r10_build.sh`; R166 already moved to (35.25, 64)).
- Gate self-tests seed the real board (`tools/test_r10_check.py` RealBoardSeeds):
  fixture coordinates can collide with new copper; fix the fixture, never the rule.
- Fast iteration: `r10_pcb.py`, then `r10_route.py FAMILY` for core, usb, pyro,
  power, signals, ground in order (KiCad Python), then `r10_post.py`; the full
  build reruns everything plus check.sh (about 10 minutes).

Next: arrange the now-identical terminals in the intended AVA-like rows, apply the
ten adopted comparison §6 layout changes where legal, recompute final feed/current
and other geometry-bound models, rebuild and rebind fabrication. Start fresh full
review round 11 on the committed layout board with ten independent lenses, verify
confirmed Critical/Major findings freshly, fix/commit as needed, continue to two
consecutive clean full rounds on the same board, then update the complete deviation
inventory/STATUS/AGENTS. Rounds 9/10 apply to b337fe63… only.

Unverified: firmware implementation/timing, actual card write current/latency and
power loss, 20 ms selected-lot match firing, source/harness/servo return, gate/ADC
transients and cold bands, hot-plug pin waveforms/damper durability, thermal/current
fault behavior, RF immunity, physical harness/card/lid/sled/shroud/battery fit,
shock/vibration/retention, coating/opaque-cover tests and assembler process approval.
Cost/stock evidence must be current before ordering; nothing is ordered or accepted.
