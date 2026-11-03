# Round 16 — independent gate adversary

Target commit `b1b8658d5bf541795b7e7636c09f2e886ea8c67a`; PCB before and after:
`632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`.
All 1,942 frozen tracked files remain unchanged. Result: **0 Critical, 0 Major,
2 Minor**, both new prospective validation defects. No current hardware failure
or AGENTS section 2 violation is demonstrated.

AGENTS, both target/review packets, steer, REQUIREMENTS, all 119 decision IDs,
the 22 amended owner scopes, AVA_LAYOUT, M3_R10, current R10_VALIDATION and its
deviation inventory, R9 severity precedents, and the read-only VEHICLE/handoff
were considered. AUD-2 affects only its named return checks; AUD-10 affects only
its named representations/distance; GAP-3 remains exactly two specified vias.

## R16-GATE-01 — saved binding evidence can be wrong while the complete gate passes

**Minor; new; open.** `tools/check.sh:47` dispatches the board checks but never
compares the saved `sources/r10_design/r10_binding_note.json` with native
regeneration. `tools/test_r10_check.py:285` checks a newly generated object,
without the board argument, rather than the saved evidence. The fabrication
manifest also does not bind this JSON.

A complete 1,942-file copy was verified byte for byte against the freeze before
the unchanged control. Its ordinary `tools/check.sh` exited **0**. Only the saved
binding note was then changed:

| JSON member | Valid control | Seed |
|---|---|---|
| `board_sha256` | current PCB hash | 64 zeroes |
| `u1_pins/3/net` | `PYRO1_GATE_N` | `GND` |
| `imu/roll_about_forward_axis` | `-gyro_Y` | `+gyro_Y` |

The same complete gate again exited **0**. Both runs used official CLI 10.0.7,
native API 10.0.6, the complete project/rules/local libraries, and the normal
manifest and self-tests. DRC/unconnected/parity/ERC were all zero; all 31 rules,
fit and routing passed; the real copied-root manifest checked all five outputs.
No executable result, CLI or gate stage was substituted. A final hash comparison
shows the binding JSON is the sole changed frozen input in the copy.

The original saved note equals `r10_sch_check.binding_note(project, board)` exactly.
Original/seed note SHA-256:
`35a72d796c7a6dd51eb1dc32f652c9c9f702f07121c466eb5d117e494ab392bf` /
`2cdacaf68d383f78645efa6e2c912a43a3f045be3718da775df818aa6a75dc62`.
Control/seed complete-gate log SHA-256:
`a75c833eecb87bc10f9b215d4446b07c65a4a7594635025166927b94c3520279` /
`06fc727b6056cfcfe655052700ba56f2f8e6d0e6300aeabf3ba3a89146a14e19`.

**Fix:** compare the saved note with fresh native regeneration in the final gate;
independently reject missing/stale hash, wrong pin facts and wrong axes. Keep the
record-only status and existing electrical/policy checks. This is an actual
complete `check.sh` artifact escape, **not** an executable-firmware failure or a
demonstrated escape from the complete source-build/release workflow. A build
regenerates the note; R10 firmware remains absent/R1-bound as already disclosed.

## R16-GATE-02 — exact duplicate representations still cause blocking topology failures

**Minor; new; open.** `tools/route_check.py:1894` and `:2173` analyze duplicate
segments as independent branches/edges before `gated()` exempts only their
`duplicate_segment` annotation. This conflicts with D-AUD-10's exact-duplicate
scope. The regression at `tools/test_route_check.py:955` filters the scan to
review categories before evaluating it, so cannot observe collateral failures.

Fresh native scans of the unchanged real target have **0 failures**. Adding only
an exact second representation of `GPS_RX_MCU`, F.Cu, width **0.2 mm**, from
**(28.8,24.2) to (28.8,11.0)**, length **13.2 mm**, leaves the copper union unchanged
but adds **two blocking `fold_back` findings** at those endpoints and **one
blocking `track_loop`** at **(28.8,17.6)**. The duplicate annotation itself is
correctly informational. A new native synthetic 10 mm straight route reproduces
the same two-fold-back/one-loop behavior; its unchanged control has no failures.
A separate 2–8 mm partial-overlap seed remains blocked as required.

**Fix:** collapse only truly identical net/layer/endpoints/width geometry for
topology, path-length and loop analysis while retaining the duplicate review
count. Evaluate the entire scan in the AUD-10 regression. Preserve partial
overlap, crossing, connectivity and genuine-loop failures. This is a proven
local false rejection, not a whole-gate escape. No duplicate was added to the
canonical board, and no seeded-board DRC or complete gate is claimed for it.

## Additional fresh controls

Positives use unchanged target geometry/artifacts, except the explicit synthetic
alias and route fixtures, and pass the named check. Negatives are genuine in-memory CAD/artifact seeds;
they do not establish a complete-gate escape.

| Boundary | Actual negative result |
|---|---|
| C126 DNP; R128 changed to 1 GΩ | S-4 and S-3 reject respectively |
| Direct pack-to-RAW_ACT B.Cu bypass | S-2 names J1.1 BAT_IN reached from RAW_ACT |
| Copper across J400.1/J400.2 | S-5 explicitly reports both switch-contact bypass directions |
| Third U401.11 thermal via | GAP-3 rejects count 3; valid control qualifies exactly 2 |
| In2 graphic 0.500 mm from J121.1 hole wall | S-8 rejects against unchanged 1.000 mm floor |
| RAW_PROTECTED width 0.150 mm at B(18.75,79.80) | K-width rejects against 0.300 mm floor |
| BAT_IN feed width changed to 0.900 mm | F9-1 rejects stale board-derived/electrical inputs |
| Remove GND partner (32.799999,11.5) | GPS_RX_MCU transition (32,11) companion distance 0.943397→2.563201 mm; UART remains in the required set |
| J410/J430/C84 model x scale ×0.99 | All fail reviewed normalized physical bounds |
| Contradictory MPN alias; R134 ordered with R166 identity | Identity audit and native-bound BOM walk reject |
| Native paste aperture D11 widened 0.010 mm | 8 geometry mismatches reject; original 245 top/373 bottom apertures all match |

The complete gates ran 176 R10 tests with four native NumPy skips and separately
passed their two mandatory numerical tests. A fresh supplied-NumPy invocation
of `HotplugNumerics Plate` passed **all four** skipped cases. Fit31, paste16,
parts5 and routing60 also passed in each complete gate.

The first optional pack-bypass sketch used F.Cu against bottom-only R134.2 and
did not form the intended connection; its empty S-2 result is rejected as an
invalid fixture. The corrected B.Cu seed is detected. No local-stage miss from
that initial sketch is claimed. Probe sources, raw results and full-run receipts
are in the owned ignored `.supervisor/r16_gate_probe/` directory; their hashes
are embedded in the JSON report.

## Limits and rejected severity hypotheses

The saved binding is correct today; an incorrect note accepted by `check.sh`
does not execute firmware. Therefore a Major/Critical firmware-failure reading
of R16-GATE-01 is rejected. Safety-omission, direct-battery-feed and inner-barrel
fault hypotheses were rejected on their actual positive/negative results above.
No unreported current Critical/Major candidate remains.

No canonical build/full gate, CAD/fab/source edit, Git operation, peer-current-
round read, other-worktree write, GUI bypass, physical test, firmware execution,
new supplier query or full 2,304-case numerical rerun was performed. The gate
validated the current board-bound hot-plug evidence and rejected changed feed
copper; this does not independently requalify its physical model. Correctly
disclosed VCAP/DB125, process, retention, installed RF, pulse-tail, SD and firmware
obligations are not converted into demonstrated failures. The attempted external
Ucamco PDF fetch timed out and is not used as evidence. No maker parameter,
manufacturing process or flight qualification is inferred from these probes.
