# R10 offline diagnostics

This host tool interprets saved voltage and harness records for **M3-ASSY-R10**.
It does not connect to a board or run firmware. Live USB/SWD capture remains
bound to R1; no R10 firmware or physical board has been qualified.

Run from the repository root with Python 3.9+ on macOS/Linux (standard library
only; file reads require POSIX no-follow/nonblocking support):

```sh
python3 -m diagnostics.r10_offline template --board m3_design/assembly_review/m3.kicad_pcb > my-record.json
python3 -m diagnostics.r10_offline manual my-record.json --board m3_design/assembly_review/m3.kicad_pcb
# Machine-readable report:
python3 -m diagnostics.r10_offline manual my-record.json --board m3_design/assembly_review/m3.kicad_pcb --json
# List native points with their GND references; --json retains full identities:
python3 -m diagnostics.r10_offline points --board m3_design/assembly_review/m3.kicad_pcb --json
```

The template intentionally has no measurements and an invalid `[0, 0]` source
reference placeholder. Fill in the actual assembly, session, stable configuration,
observation window and instrument records. Use a new file for each session.
The program only reads files and prints reports; it does not overwrite evidence.

For a format demonstration, use
`diagnostics/examples/r10_offline/example_manual.json` in place of `my-record.json`.
**Every observation in the example is invented to demonstrate the format.**
Do not reuse it as an acceptance record or relabel it as a physical measurement.

## Evidence and interpretation

- Each board voltage needs the complete point and GND identity, volts, a closed
  interval, positive absolute uncertainty, instrument, timestamp and uncertainty
  basis. The interval must enclose the declared ± uncertainty. A module-terminal
  voltage uses its installed port and terminal names, without invented PCB XY.
- Measurements must agree on assembly, session, epoch and configuration and lie
  within the stated time window. Missing or unavailable readings are never zero.
  Repeated readings do not shrink uncertainty; conflicting readings stop voltage
  localization. A separately validated earlier unpowered continuity record can
  still identify a UART line-order mismatch; the report retains the voltage
  conflict and does not infer a power fault from it. The supplied source window
  is an operator declaration, not a verified instrument or device rating.
- The JSON report keeps each original observation in `observation_records`.
  `observed` contains separately labelled conservative envelopes, without an
  instrument, timestamp or pad attribution. Consistency is checked across every
  contributor, so a bridging interval cannot hide mutually contradictory records.
- Supply localization needs a known single source and recorded assumptions about
  steady state, ground, backfeed and external self-power. Ambiguous source states
  remain unresolved. Supply inference covers the recorded steady state only.
- Camera EN certainty uses the retained enclosure, never the declared error as
  an electrical bound. OFF requires the full interval within 0–0.66 V; ON requires
  1.1–6.5 V, per [TI TPS2553 SLVS841G §6.3/§6.5](https://www.ti.com/lit/ds/symlink/tps2553.pdf).
  A near-zero interval extending below the recommended input domain stays unknown.
  These are conditional logic screens, not physical switch qualification.
- UART line-order findings require an earlier **unpowered** continuity record,
  bound to the same board/assembly/session, with an unchanged harness. DC voltage
  alone cannot establish a UART wiring fault or communication functionality.
- A result names supported branch, feed, load or harness possibilities and gives
  native pad/net/side/XY plus a GND reference. It cannot identify a failed IC from
  a voltage alone. `LOCALIZED` does not mean all faults have been found.
- `NO_DEMONSTRATED_FAULT_WITHIN_OBSERVATIONS` applies only to the recorded screens.
  It is not a board PASS. Missing voltages and unverified functionality remain
  visible; `physical_qualified` and `firmware_verified` stay false.

J410/J420/J440 share the always-on peripheral rail and accept any permutation of
GPS/radio/AUX. They have no individual power switches: 1 supply, 2 GND, 3 board
TX/module RX, 4 board RX/module TX. **J9 differs:** its supply is the camera rail,
and 3 is board RX/camera TX, 4 board TX/camera RX. Do not interchange J9 with the
other ports. Module TX compatibility with the direct ports' 3.6 V ceiling remains
unverified. The tool does not command power, change wiring, or test outputs.

## Native board binding

Both the supplied PCB bytes and the catalog content are SHA-256 pinned. The PCB
is `6d23d1e5ca477a9754b55a8830fee6e4554b6cb74903593de075c0ede7b60153`.
`tools/check_r10_diagnostic_profile.py`, run by `tools/check.sh` using KiCad Python,
compares all 33 catalog points to the actual native pad identities and coordinates
and verifies the 216-footprint / 705-pad inventory. A different PCB requires an
explicitly regenerated and reviewed profile; the tool never guesses a revision.
File identity does not prove the assembled hardware matches it.

All XY values use the **PCB top projection**: x right, y down, millimetres.
Bottom pads are not mirrored. Native identities do not qualify physical probe
clearance on an assembled, mounted or coated board.

For bounded MCU register capture and a report paired to the same instrument
session, use the separate [R10 SWD workflow](R10_SWD.md). Its six J2 pads are
also compared against the native PCB by the project gate.

## Software checks and synthetic replay

```sh
python3 -B -m unittest diagnostics.test_r10_offline
python3 -B -m unittest discover -s diagnostics -t . -p 'test_*.py'
```

The library provides `Profile`, `analyze_manual`, `render_zh` and a synthetic
`Session` interface. With no arguments, `r10_offline.py` accepts one JSONL session
using `r10_protocol.schema.json`: initial → probe/measurement → result, at most
six additional observations (unavailability counts). This mode accepts only
`SYNTHETIC_FIXTURE`; it authenticates no physical board. Early EOF is an input
error, not a completed diagnosis. Software checks and synthetic cases do not
verify startup, transients, temperature, sensors, storage, communications or flight.
