# R7 step B — running log (board placement and routing)

Successor notes: read this top to bottom; the newest entries are at the end. Scripts live in `m3_design/`
(`r7_build.sh` runs them in order). Nothing is committed (owner rule for this step).

## 0. Starting state (verified 2026-10-15)

- Worktree `rocket-flight-computer-r7`, branch `m3-assy-r7`, HEAD `3b215ba`.
- `m3_design/assembly_review/m3.kicad_pcb` = committed R6 board, SHA-256
  `184a87e84e67576341244c82517de3e9f55f5c1c22995dfad83631d48c856680` (checked).
- Step A outputs (schematic, netlist, libraries) uncommitted, ERC 0 per `stepA_handoff.md`.
- Tools available: KiCad 10.0.6 (`pcbnew` Python, `kicad-cli`), Freerouting 2.4.1 at
  `~/.local/share/freerouting/freerouting-2.4.1.jar` with Homebrew OpenJDK 27 (`/opt/homebrew/opt/openjdk/bin/java`).

## 1. Builder stage 1 (`r7_pcb.py`, `r7_lib.py`)

- Rigid +18.0 mm translation of every board item; outline 46 x 118; aft supports moved to (4, 4) and (42.3, 4).
- `r6_pcb.synchronize()` re-used for the netlist import (37 refs removed, 38 added, no footprint replaced).
- Removed nets (26, asserted to be only TLM_*/GPS_*/old RADIO_*): 564 tracks/vias deleted; then 39 dangling
  items of the shared nets 3V3/GND/RAW_PROTECTED/PULLPIN_EXT deleted by a DRC-driven loop (only items KiCad
  reports dangling, only on those nets).

## 2. Findings that shape the routing (measured on the translated board)

- **U1's radio/GNSS pins face the power-input area.** Pins 51-57 (SPI2 etc.) and 61/63-65 (GNSS) are on U1's
  left side (x 13.5-15.1 pads, y 47.5-54.5). West of them: QSPI_IO0 runs on F.Cu along the pin tips (x 12.9,
  y 42.5-51), the VLOGIC hold-up rail runs on B.Cu (x 11.0-11.9, y 36.4-57), C84 (OS-CON) and its GND
  diagonal, BAT_ILIM, BUZZ_DRV, BAT_FAULT_N. A greedy grid-router trial (scratch) escaped only 3 of 12 pins.
- **Existing copper inside the planned strip:** BAT_SW_SOURCE (B.Cu down to y 20.8), BAT_SW_RETURN (y 21.9),
  CAM_MCU_TX (In2, y 20.85) and LED_RED (B.Cu, y 23.95) loop through the old port area; all must leave the
  strip (y < 23.5).
- **J123 at the decided (36.0, 34.5)** lands its two THT pins on VLOGIC_SENSE (via and tracks), LED_YEL,
  PULLPIN and a CAM_5V track; those non-critical nets get re-routed round it, or J123 shifts locally.
- **Chain length vs courtyards:** the jack courtyard ends at y 4.695 and the U30 courtyard (12.5 mm paste span)
  starts at y 8.505 (U30 at the planned centre y 14.95); five RF parts in series need about 5.2 mm. Each pi
  network is therefore laid as one row across x (0 ohm along x, a shunt beyond each pad), which puts the
  module RF pin 0.86 mm east of the jack axis: U30 centre x 10.41 (plan 9.55), U31 centre x 29.86 (plan 29.0).

## 3. Interface routing plan (decided after the escape experiments)

- **Topology:** every U1 radio/GNSS line must cross the VLOGIC hold-up rail (B.Cu, x 11-12) to reach the
  aft-left corner. The only clean corridor is B.Cu along the left edge (x 1.2-6.2, y 24-52; In2 below it is the
  BAT_IN plane, F.Cu above it holds only parts). Trial (scratch `exp/try2.py`): with the surgery below, the grid
  router escaped 5 radio lines west on F.Cu; a structured layout is needed for all 11.
- **Surgery at U1's left side** (recorded per item when built):
  - QSPI_IO0 (critical, F.Cu along the pin tips x 12.9, y 44.4-51): replaced from pin 58 by an inward stub, a
    via under U1 (15.55, 50.85), B.Cu west along y 50.85 and down x 12.9 to a via at (12.9, 44.4), then the
    unchanged F.Cu route to U3. Same layer pattern as QSPI_IO1/IO3 (B.Cu over the In2 3V3 plane).
  - VBUS_SENSE: inward escape (via at (15.65, 53.0)) and a short In2 link to its existing In2 run; frees pin 61/63.
  - C84 GND diagonal F.Cu trace (pad -> (11, 50.45) -> via (11, 53.55)) replaced by GND vias at the pad; frees
    F.Cu under C84 between its pads (y 49.3-53.3).
  - GND stitching via (12.7, 53.7) and stray GND B.Cu stubs near C80 removed (the pours still connect; checked by DRC).
  - C80's BAT_IN via (9.43, 52.1) moved to share C96's via (9.3, 53.38) with a 0.5 mm B.Cu link.
  - Ripped and re-routed afterwards (non-critical): BUZZ_DRV, BAT_FAULT_N, LOGIC_SOURCE_ST, BAT_SW_SOURCE,
    BAT_SW_RETURN, the BAT_ILIM test-pad branch, CAM_MCU_TX/RX and LED_RED where they cross the new paths.
- **Escape:** radio pins 51-57 straight west on F.Cu (R313/R315 inline at x 12.25) to vias at x 9.3/10.0 (rows
  47.5-50.5), then B.Cu west to corridor columns x 6.2..3.2. GNSS pins 61/63/64/65 west on F.Cu (R306 inline),
  jog aft to rows 51.0-52.5 under C84's body, vias at x 2.7..1.2, B.Cu columns.
- **Corridor bottom:** GNSS turns east on B.Cu at y 24.1-25.75 and comes up to F.Cu at U30's forward pins
  (RESET_N stays on B.Cu under the others); radio turns east on B.Cu at y 27.2-30.2, vias at x 9.4/10.0, then an
  F.Cu band (y 27.2-29.6) east to x 18.6-22.2. DIO1/NRST drop to B.Cu (y 24.3/24.8) and run east to pin 20 and
  round the east side to pin 3; the SPI group turns aft into the strip at x 20.6-22.2 (>= 5 mm from U30), with two
  swaps (MOSI/MISO, NSS/SCK) by via hops near the module.

## 4. Builder and routing decisions made while building (each with its basis)

- **Port parts deleted before the netlist import, without their leadouts** (`r7_pcb.py`). Basis: deleting their
  leadouts first (as `r6_pcb.synchronize` does for removed refs) cut T-joints of live 3V3/GND copper that rode on
  them (C100, C23, R164 lost 3V3). Now only copper DRC calls dangling is touched, and a dangling track is trimmed
  back to its last joint (`r7_lib._trim_or_delete`) rather than deleted. Stage 1 result: 688 tracks/vias of the
  26 removed nets, 21 shared-net items deleted, 1 trimmed; the only unconnected items left are the new parts.
- **J123 at (36.0, 34.6), not (36.0, 34.5).** Basis: at 34.5 its pin 1 is 0.1 mm short of clearance to R6's
  CAM_5V branch (R104 -> U13); 0.1 mm forward clears it by 0.2 mm without rerouting a supply track (pass1_layout
  L13 gives the position as a move target, not a measured constraint).
- **Module x shifts +0.86 mm** (U30 10.41, U31 29.86) and the pi rows laid across x (section 2).
- **Fence at y 23.3, not 23.5.** Basis: the fence vias must sit inside the strip pours (strip edge y 23.5,
  via 0.6 mm, pour clearance); openings at x 6.3-12.4 (GNSS leads, FB30 feed) and 20.0-23.8 (radio SPI lanes).
- **Option-B escape with the MISO/MOSI escape order swapped** and R313/R315 (SCK/MOSI 33 ohm) inline in the left
  corridor rather than at U1 (no room between U1's pins and the via row). Basis: section 3 trials.
- **B.Cu inside the strip carries three radio signals** besides the limiter nets: the TXEN loop (x 24.5,
  y 7.8-20.15), DIO1's lead (x 32.4, y 20.15-24.0) and NSS's hop under SCK (via (23.2, 17.3) to (23.6, 15.27)).
  All are outside U31's keep-out; In1 under them is solid GND. `tools/check_r7.py` lists the allowed nets.
- **FB31 fed on F.Cu** from R161.1's 3V3 pad (0.4 mm link). It first also had an In2 band via at (35.1, 25.1);
  that went with the band (section 5).
- **C84's GND** now reaches In1 through three vias at x 9.0 beside its pad (its R6 diagonal blocked the escape).
- **R6 copper of 13 non-critical nets redrawn** (BUZZ_DRV, BAT_FAULT_N, LOGIC_SOURCE_ST, BAT_SW_SOURCE,
  BAT_SW_RETURN, LED_RED, LED_YEL, CAM_MCU_TX/RX, PULLPIN, PULLPIN_EXT, VLOGIC_SENSE, BAT_ILIM): their pieces in
  the strip, in FB30's In2 lobe or in DRC conflict with the new copper are deleted (`clean`), the connections
  redrawn by the house grid router (`reroute`, recorded as a session, section 5), the rest left hanging pruned
  (`finish`). No Freerouting session is used.
- **D30.2 / D31.2 get explicit thermal relief** like every small R/C GND pad (house policy in check_r7).
- **TP30 SAFEBOOT legend window**: the strip lattice skips (0.85-2.05, 10.75-22.65) so the legend fits up the
  left edge beside TP30 (the 2 mm lattice leaves no 1 x 12 mm spot otherwise).
- **VBUS_SENSE In2 link** joins R6's In2 run at its exact end (13.6118, 53.5831), not 2 um off it
  (check_r7's overlap-only joint test).
- **m3.kicad_dru**: R7 rules (RF width/gap, SMA launch gap and edge clearance, module keep-outs) added before
  the pyro rules; pyro blocks unchanged (check_actuators hashes each); the whole-file pin DRU_SHA updated.

## 5. Completing the reroute (the displaced non-critical links)

- **First attempts (scratch, 12 net orders, 15 min each):** the grid router always left 3 connections open,
  rotating among BAT_SW_RETURN, BAT_SW_SOURCE, PULLPIN_EXT, BUZZ_DRV, LED_YEL and CAM_MCU_TX. A forced rip-up
  phase (`_force`: draw across the displaced nets' copper, redraw what it cuts) only traded one open link for
  another. Freerouting 2.4.1 restricted to the 13 nets (DSN network cut to them) left 11-13 of 15 open. Basis
  for the diagnosis: R6 ran these east-west links through R6 y 0-5.5 (R7 y 18-23.5), which is now strip; the
  only east-west room left forward of the strip (R7 y 23.5-27) was taken by the In2 3V3 band, the B.Cu
  DIO1/NRST runs and the F.Cu interface band.
- **Fix: the In2 3V3 band shrank to a lobe round FB30's feed via (x 9.9-14, y 23.9-27).** FB31 already had a
  0.4 mm F.Cu link to R161.1's 3V3 pad (whose own R6 via and 0.25 mm In2 trace reach the plane; about 33 mOhm,
  about 4 mV at the radio's 119 mA transmit current: calculation, Inference), so its band via was dropped. With
  In2 at y 23.5-27 free, all 6 orders tried left 0-1 open.
- **Two side fixes found on the way:** a GND via at (32.2, 27.033), the end of R105.2's R6 GND stub (a route
  cut its B.Cu pour patch off in one order and no island via fitted afterwards); `_dedupe` drops new tracks that
  retrace R6 copper (BUZZ_DRV's waypoint legs had doubled an R6 piece and left a stub dangling); the R6 prune now
  trims a track back to the joint a new route made on it instead of deleting it (deleting whole tracks had
  reopened 9 connections between sweeps).
- **Result:** order BAT_ILIM, VLOGIC_SENSE, BAT_FAULT_N, LED_YEL, BUZZ_DRV, BAT_SW_RETURN, PULLPIN_EXT,
  CAM_MCU_TX, LED_RED, LOGIC_SOURCE_ST, CAM_MCU_RX, PULLPIN, BAT_SW_SOURCE (r7_route.FIRST): 12 connections
  drawn, 8 using In2, nothing open, DRC clean. One PULLPIN end landed 7.5 um outside D122.3 (house joint rule):
  finish adds a 0/90 degree stub into such pads (`_pad_joints`).
- **The result is kept as a session file** (`m3_design/r7_reroute_session.json`, 10 R6 items removed, 239
  tracks and vias added, nm coordinates), replayed by default and checked against a digest of the pre-reroute
  board, like R5's Freerouting session. `r7_route.py --search` regenerates it byte for byte (checked).

## 6. Final state

- `m3_design/r7_build.sh` from the R6 board: about 75 s; two runs give the same board,
  SHA-256 `03fe75720f46b1382d9d3216dbffd8ae642d0125722c04589ff97c964aa86d54`.
- `tools/check.sh`: DRC 0, unconnected 0, parity 0, ERC 0, metadata/3D OK, silkscreen OK, R7 CAD contract OK,
  actuator safety contract OK, fit check OK.
- Tool tests: check_shell, fit_check, maze_clearances, procurement, r6_check, r7_check pass;
  `test_fab_validation` fails (7 F, 1 E) only because the fab package (CPL) and the JLC placement corrections
  are still R6's (step C); `test_r5_repair` fails on the committed R6 board too (pre-existing).
- Renders: `r7_top.png`, `r7_bottom.png` (984 x 2184, kicad-cli, high quality). Handoff: `stepB_handoff.md`.
