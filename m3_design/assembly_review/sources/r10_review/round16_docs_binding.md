# R16 lens10: documentation and firmware binding

Fresh full independent review of commit `b1b8658d5bf541795b7e7636c09f2e886ea8c67a`, PCB
`632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`.
**0 Critical / 0 Major / 2 Minor.** All1942 frozen canonical files and the PCB
hash are unchanged before/after. No Git command, canonical/other-worktree write,
current R16 peer exposure, subagent, owner question or GUI retry.

## Findings

| ID | Severity/status | Evidence and impact | Concrete fix |
|---|---|---|---|
| R16-DOC-01 | Minor,new | `sources/r10_design/r10_plan.md:5-11` explicitly labels R14/`7866d6b8`,957segments,fresh15/16 and D-R11..D-R14 as current. Native PCB is`632a9ad3`,951segments; fullR15 reviewed the predecessor and current records require16/17/119IDs throughD-R15-03. A reviewer following the plan receives the preceding target/round pair. Correct current headers/bindings elsewhere prevent a demonstrated false release. | Refresh that current plan header/pointer from the existing R15 integration and current exact PCB. Preserve its historical body. |
| R16-DOC-02 | Minor,carried | Read-only `../../docs/VEHICLE.md:39` still gives GH-4 ports,ARM/IGN terminals,GH-2J400 at(10.5,85.5) and0.03mm mated-GH margin. Native J400 is DB125-2F(7.4,65.85); all seven wired terminals are DB125 and J123/J124 are absent. The local vehicle handoff already supplies correct replacement facts. | Apply that R10-only replacement through the separately authorized parent-document workflow; preserve acceptedR9/OQ-7 and pending physical fit. No other-worktree edit in this review. |

## Fresh evidence

- Read AGENTS first, packets/steer, requirements, complete decisions through
  D-R15-03 and mandatory current/history sources. All119 decision IDs/titles/source
  lines and22 owner scopes reconcile under their newest amendments.
- One root-reserved official native schematic export exits0. Bundle10.0.7,
  CLI SHA256`0b9d96dbdac9517e7d85833f926fee07a563549ffe2c55670147bff3f562d01f`.
  Its209 component identities/fields/flags and651 unique reference-pin nets equal
  the saved XML. All651 maps equal the fresh PCB API reconstruction;663 numbered
  physical pads collapse by12 duplicate fingers. All100 U1 ports/nets agree with
  the sole r10_net table and evidence note.
- Fresh API10.0.6 confirms209footprints/951segments/296vias(168GND),
  1788.675664583mm track, all seven terminal poses/roles, J430B(24,24.3),
  118visible/91hidden references and40legends. The removed hardware stays absent.
  Independent gate-network inspection agrees with separate PC1/PE4 controls and
  post-Q121 RAW_ACT/R134 feed. This does not qualify reset or firing behavior.
- The four note digests match PCB/XML/table/circuit. In-memory binding note and
  native-bound parts budget regenerate identically. Independent quadratic
  arithmetic gives1.544366071699..1.283013039049A at0..4persistent stalls;
  960LSIcycles gives28.571428571..32.653061224ms and the34.853061224ms allocated
  fault bound. Single top-short OR bottom-open divider calculation gives
  3.342170829V under the named tolerance/temperature assumptions. O6 gives0.6144A.
- Fresh hot-plug extraction has exactly the saved canonical JSON digest and
  electrical signature. Saved2304required+60local rows, source/input binding,
  limits and convergence validate without issues. No numerical sweep rerun.
- The five-output manifest verifies against193 current inputs.82BOM codes have
  199unique references with correct quantities; CPL has those199,67top/132bottom.
  Frozen supplier arithmetic reproduces79.5232USD placed/feeder share and
  81.3254USD with minima. R430/U4 stay short.13:13supplier time remains distinct
  from14:59record rebinding; no new quote/query/order is implied.
- All139 ledger catalog aliases reconcile:123 exact current hashes,3 historical
  prefixes,13 explicitly archived scopes.698 source links have696 resolved JSON
  pointers and2 source-scoped/nonJSON links, no bad/unknown pointer.64embedded
  original findings match immutable reports;46historical groups/229row IDs and
  ordinals reconcile. Old Git blobs were not retrieved under the no-git rule.

## Sources, applicability and rejected hypotheses

[ST DS12110 Rev11,January2026](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf)
was checked live for the selected UART/SPI alternate functions,input restrictions
and LSI range. The exact named H743 cache is Rev8 and was excluded as Rev11 proof.
Full [ST DS14623 Rev1 p9](https://www.st.com/resource/en/datasheet/lsm6dsv320x.pdf)
was rendered/inspected: native U4B180(17,45.9),pad1offset(+1.21,-0.75),leverx-6mm
agree with roll=-gyroY/thrust=-aY. Leverz-2.06 remains model-derived Inference;
the documented board frame is left-handed, so rotations use the IMU frame.

No false executable R10 binding, current pin/connector/axis mismatch or actual
AGENTSsection2 violation was found. `assembly_binding.py`/protocols/build options
remain R1; build.py has no R10 target and retains its legacy IMU/hash guards.
The regenerated R10 JSON explicitly records evidence only. No executable firmware
was built or run. Current requirements correctly retain always-on GPS/radio,
camera-only isolation,one direct bus bank,no ARM link/pull-pin,off-board servo
power,optional plate and conditional LED-cover permission.

Current records explicitly retain VCAP combined-condition/ESR and DB125
insertion/S8 fabrication allocations. Those disclosed qualifications alone do
not demonstrate a present hardware failure. Historical aliases/clean pairs remain
source-scoped; current completion denies transferred pair credit/owner acceptance.
The JSON preserves all rejected C/M hypotheses and remaining limits.

This lens did not run canonical builds/fullcheck,PCB DRC/ERC,numerical hot-plug,
plate,full orientation/paste suites or manufacturing visual QA. It separately
states fresh executions and hash-checked receipts. Firmware,SD/e-match lot,
electrical/thermal/transient/endurance,installedRF/ESD,harness/tool/hinge,
coating/retention/bore/stack/flight and first-article/process remain unqualified.
R9 stays accepted; R10 remains unaccepted/unordered with stock,quote/process and
owner deviation acceptance pending. Reports are immutable after handoff.
