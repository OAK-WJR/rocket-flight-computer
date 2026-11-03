# Local and GitHub integration, 2026-11-02

Local input: `mit-review` at `8819bd2abe2cc2aaca65804454f4366f6f37366b`.
GitHub input: `m3-assy-r10` at `deb179eb74183402895cc02b877ab8a24d078aa3`.
Shared ancestor: `18de45a` (main / R2).
Integration branch: `merge/r10-local-20261102`.

The merge preserves both parent histories. The board, schematic, project-local libraries, fabrication package, build scripts and firmware are taken unchanged from the R10 parent. No circuit or routing changes were made by this integration.

Conflicts resolved:

- `.gitignore`: keep both the local secret/agent-state exclusions and the upstream failed-build exclusions.
- `README.md`: use the R10 project entry and current navigation; preserve the local design-only statement, per-tool credits and link to `THIRD_PARTY_NOTICES.md`. Historical R2 images and tests are not presented as current R10 evidence.
- The local third-party notices and the deletion of three copied datasheet-page images remain in place.

R10 board SHA-256: `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`.

The local KiCad CLI is 10.0.6; the committed R10 netlist was exported with 10.0.7. Regenerating the full source project showed exactly one changed line: the exporter version in `design/tool`. The schematic-reproduction checker now normalizes only the 10.0.x patch number in that element. Every other netlist byte and all schematic/DRU bytes remain compared exactly. Ten focused tests retain detection of changed pins, nets, values, supplier identities, sheet names and unsupported minor versions. The shell-gate test includes the new test stage and its failure propagation.

The preserved local plot script and two portfolio images are R2 history; copied datasheet pages stay removed. All R10 CAD, libraries, fabrication payloads and firmware remain byte-identical to the R10 parent.

Checks are recorded after running `tools/check.sh`. A passing CAD/software gate is not a hardware test, fabrication approval or acceptance of the R10 deviations. Existing R1 firmware stays R1-bound.

No remote branch is updated by this local integration.

## Completed checks

`tools/check.sh` completed with exit code 0 on the normal macOS user session, using KiCad10.0.6. DRC, unconnected items, schematic parity and ERC are all zero. Schematic replay, model/metadata, fit, routing and fab-content/binding checks pass; all required regression stages complete. The earlier sandbox-only DRC-seed crashes were reproduced and both subcases passed under the normal user session without changing CAD or weakening DRC rules.

The default isolated system Python lacks NumPy, so its six numerical tests are skipped. Those same six tests were also run in an isolated temporary NumPy2.0.2 environment and passed without skips; the separate result and log hash are recorded in the evidence.

Machine-readable results: [integration checks](INTEGRATION_CHECKS_2026-11-02.json). The unchanged R10 board is still a CAD candidate, not accepted or hardware-qualified.
