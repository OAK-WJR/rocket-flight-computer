# R10/R11 integration and two-board purchasing budget

The owner requested merging R11 and every current non-main branch, preserving
normal history and leaving main unchanged. At the read-only remote inspection,
`m3-assy-r10` was `deb179eb…`, `m3-assy-r11` was `1dc2194a…` and
`r10/offline-diagnostics` was `e0dded5c…`. R10 is already an ancestor of both other
development lines; one normal R11/diagnostics merge includes all three. Original
authors and commits remain; no squash, rebase or force push is required.

## Board and firmware scope

- R10 remains `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `6d23d1e5ca477a9754b55a8830fee6e4554b6cb74903593de075c0ede7b60153`.
- R11 remains `m3_design/r11/m3.kicad_pcb`, SHA-256
  `5f1a7e1dfcae95a3ebe06801cc74dc366aa83f477b416e25e72649f4365d2b63`.
- Both schematic netlists contain216 reference identities and121 named functional
  nets. Non-MCU connectivity differences are J9's duplicated supply/ground pins
  and UART contact numbering. This comparison does not prove electrical,
  mechanical or firmware equivalence.
- R11 exchanges the LQFP MCU for BGA, changes38 resistor and13 capacitor packages,
  exchanges eight connectors and reassigns multiple MCU functions. Its camera
  GH-6 is not the owner's earlier four-position screw-terminal requirement.
  That interface change has not been accepted merely by merging the history.
- R10 diagnostic firmware remains bound to R10. No R11 firmware, image scheduling,
  diagnostic record qualification or physical testing is supplied by this merge.
  The SD native transport is standalone and not linked into the ABI5 image.

Conflict resolution retains the strict R10 netlist metadata comparison and both
revisions' gate/self-test families. The combined shell suite checks that neither
family can disappear or silently skip required stages. Full gate evidence is
required before committing; CAD and software checks are not first-article tests.

## Owner ceiling: US$200 for two usable boards

The ceiling applies to two complete usable boards, not bare PCBs or a partly
populated quotation. Shipping and US duties/tax are included as a conservative
working assumption; their actual amounts remain unquoted. External servos,
camera, GNSS/radio modules and laboratory equipment are not part of the board
quotation and must be disclosed separately if purchased.

The observed R10 quote was$399.66 before shipping/tax: PCB$33.42, components
$148.53 and the remaining assembly/process charges$217.71. Feeder loading$119.35,
setup$51.50, stencil$16.54 and fixtures$16.54 account for$203.93 alone. This was
an observed quote, with final manufacturing options still unconfirmed.

R11's existing `m3_design/r11/fab/cost_check.json` is a five-board price snapshot
at2026-11-03T23:01:53Z. Reusing its unit rates optimistically for two boards gives
$113.28 for factory-fitted parts, or$127.01 when supplier minimum purchases are
applied. Its75 charged codes ×$1.53 plus$83.96 fixed fees add$198.71. The resulting
**$325.72 is only a cost screen**, excluding PCB/rails, owner-fitted C84, joints,
inspection extras, attrition, shipping and tax. It is not a two-board quote.
Neither existing full two-sided assembly path meets$200.

[JLC's capability table](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)
limits Economic PCBA to one populated side. The general prototype landing page
lists both assembly sides collectively and must not be read as double-sided
Economic support. Current boards have difficult packages on both faces; leaving
one face unselected produces unfinished boards, not a valid saving.

[JLC's fee table](https://jlcpcb.com/help/article/pcb-assembly-price) and
[prototype cost guide](https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype)
identify two cost drivers: the assembly tier and the number of charged part
codes. Standard charges all codes; Economic exempts Basic and Preferred Extended
codes. Selecting Economic requires an eligible board and an actual supplier
quote, not a renamed BOM.

The next purchasing comparison must include: full two-sided assembly; factory
assembly of difficult packages plus an explicitly enumerated manual completion
BOM; and a fully costed local-lab reflow option. Any layout/part changes need
fresh source binding, CAD checks, sourcing and process review. Manual assembly
must include equipment availability, workmanship/inspection and rework cost;
no unavailable coupon or free labour is assumed. No function or rating is
removed to make an incomplete order appear below budget.

Budget acceptance requires the real order totals plus every separately bought
part, shipment, duty/tax and necessary assembly cost to fit the ceiling. This
requirement is open. Nothing has been ordered or paid.
