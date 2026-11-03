# Round 13: documentation and firmware binding

Target commit: `fa897c81abac3026e75ca5cc88bef0c2659a7130`.
PCB SHA-256 before and after review:
`7355ae1aeb1fdfdf6f64317945a0bf114d94c2bb65fb04adfbcd5a2b8037b09c`.

**0 Critical / 0 Major / 4 Minor.** Three new bounded prose observations and the
carried parent-vehicle mirror remain. No demonstrated firmware, electrical or
AGENTS section 2 failure was found. Pending firmware/bench work is not counted as
a demonstrated hardware failure. R9 severity precedents and the target packet's
operational definitions were used; R9 has no literal severity-definition table.

## Findings

### R13-DOC-01: the final acceptance prose names the wrong O6 resistance branch

**Minor; new observation.** `docs/R10_VALIDATION.md:1231` says the 0.6144 A board
return inference uses `>=50 milliohm motor branches`. The adopted O6 calculation
instead requires each **signal-reference branch** to be at least 50 milliohm:
`R10_DECISIONS.md:102`, `parts_qualification.md:697`, and the current ORDERING
section 8.4 agree. The arithmetic is four times 7.68 mV / 50 milliohm = 0.6144 A.
A lower bound on the motor leads does not supply the required lower bound on
parallel reference paths. This is a specification transcription defect; the
ordering worksheet remains correct and no actual harness failure is established.

**Fix:** change `motor branches` to `signal-reference branches`, retaining the
1 milliohm star-transfer bound, direct motor pairs, measurement requirement and
1 A board allowance. Do not change copper or the accepted O6 topology.

### R13-DOC-02: AGENTS conflates the R10 evidence note with an executable binding

**Minor; new observation.** `AGENTS.md:26` states that both the current
`r10_binding_note.json` and `assembly binding` match `7355ae1a`. Only the generated
R10 evidence note does. `m3_firmware/assembly_binding.py:20` still returns the
`M3-ASSY-R1` profile; `verification_assembly.json:4-5` is explicitly R1 and bound
to `e432d343...`. The current R10 note separately and correctly says record-only,
R1 binding invalid, no firmware/flight approval. Its four hashes and complete
in-memory regeneration match. An import-only legacy binding probe stops on the
documented absent `check_assembly` module, before a build. No R10 executable
binding or compilation was demonstrated.

**Fix:** name only the generated R10 evidence note as matching the current PCB,
pin map and axes. State that the executable assembly-binding chain remains the
archived R1 implementation and must be replaced through a reviewed R10 firmware
implementation. Preserve the no-approval warning; do not insert a new hash into
the R1 chain. This is a provenance wording correction, not a firmware request.

### R13-DOC-03: the separately owned vehicle mirror remains obsolete

**Minor; carried from R11-m03 / R12-m02.** Read-only `../../docs/VEHICLE.md:39`
still describes GH-4 ports, an ARM terminal, GH-2 J400 at (10.5,85.5), and the
old 0.03 mm GH fit margin. Native CAD has seven DB125 terminals, no J124, and
J400 at (7.4,65.849999), facing west. Current in-worktree ordering, M3, status,
requirements and `docs/R10_VEHICLE_HANDOFF.md` correctly supersede this mirror.
The handoff is concrete and complete; the other worktree was not edited.

**Fix:** apply the handoff within the separately authorized parent-repository
workflow, preserving accepted R9 history, or mark that parent candidate paragraph
obsolete and point to the handoff. Until then retain this explicit integration
deviation. No new physical-fit failure is inferred.

### R13-DOC-04: an active harness-risk sentence retains the old Mach value

**Minor; new observation of pre-existing prose.** `docs/REQUIREMENTS.md:102`
describes flight 2's external servo raceway as operating up to M1.75. The same
file's governing source at line 13 and flight-envelope row at line 32 set the
current L1000W design point near Mach 1.9. Unlike the adjacent revision-qualified
risk rows, this sentence does not identify M1.75 as historical. The actual
retention/aerodynamic qualification remains openly pending, so this does not
establish a failed harness.

**Fix:** state the current approximately Mach 1.9 design point and label it an
estimate, or explicitly scope M1.75 to the former trajectory. Keep the final
vehicle-model, hinge-load and harness qualification obligations.

## Fresh independent checks

- Read AGENTS first, both supervisor packets, REQUIREMENTS, all 110 unique D IDs
  and their addenda through D-R12-03, r10_plan, AVA_LAYOUT, M3_R10, R10_VALIDATION,
  R9 severity precedents, the current STATUS/ORDERING/handoff/FMEA/README and
  firmware-binding sources, and the read-only parent vehicle source. No peer
  current-round report was read.
- Loaded the exact PCB through the installed KiCad Python API without saving it.
  All 209 schematic components and 651 named pad/net mappings agree with native
  pads. All 100 U1 pads agree independently across PCB, XML, reviewed table and
  binding. A separate S-expression walk derives all 100 MCU pin names and nets
  directly from native schematic symbol coordinates, wires, labels and NC marks;
  it finds no mismatch. This walk does not call the netlist exporter.
- Compared the 100 package names with ST DS12110 Rev11 Figure 5, p55, and checked
  the 28 selected alternate-function entries against Table 10, pp89-94. The
  current UART, SPI3, timer, QSPI, USB and SWD assignments agree. The five ADC
  roles, EXTI ownership and direct PC0/PC5 sense roles remain consistent with
  Table 9 and current circuit/binding requirements. [ST DS12110](https://www.st.com/resource/en/datasheet/stm32h742vg.pdf).
- Checked current bootloader resources against ST AN2606 Rev70 Table 135,
  pp320-323. Versioned Rev64 citations remain historical source references;
  the currently used loader pins and PC11 SD-MISO caveat remain represented.
  UART5/USART6 remain separate from the listed loader UARTs. [ST AN2606](https://www.st.com/content/ccc/resource/technical/document/application_note/b9/9b/16/3a/12/1e/40/0c/CD00167594.pdf/files/CD00167594.pdf/_jcr_content/translations/en.CD00167594.pdf).
- The four R10 note hashes match board, netlist, circuit and pin table. In-memory
  `r10_sch_check.binding_note()` exactly reproduces the stored note. The schematic
  component/pin contract passes and all 34 existing in-memory fault seeds reject.
  This is not a native ERC, fresh CLI export or firmware build.
- Native U4 is bottom/180 degrees at (17,45.9), pad 1 at (18.21,45.15), signed
  x lever arm -6 mm. Selected native M-7 passes with no issues. The retained
  signed map, required bench sign check and explicitly inferred z lever arm
  agree across M3, ordering, table and note. Maker axis/pin context was read from
  indexed DS14623 Rev3 Figure 5, p9. [ST LSM6DSV320X](https://www.st.com/resource/en/datasheet/lsm6dsv320x.pdf).
- Independently inspected both firing-control networks and the two direct sense
  banks in the native/XML net inventory: PC1/R122/R123/Q122 controls the
  Q120/Q121 post-switch RAW_ACT path; PE4/R126/R127/R128/C126 controls Q124;
  R134 remains 2 ohm. No J124, duplicate bus bank or R168/R170 tail remains.
  This establishes recorded topology, not measured reset/fire behavior.
- All seven terminal poses and contact roles match the current ordering/handoff.
  Native references are 118 visible/91 hidden; the current M3 hidden set matches
  exactly. No absolute native 3D-model path was found.
- The complete ledger contains every 110 unique decision ID without omission or
  duplicate, 22 owner mandates, 46 historical groups and all 229 archived finding
  rows in the same order. Read every decision's current applicability and reason.
  All 176 catalogued JSON source/pointer references resolve; all 15 catalogue
  file hashes/lengths match. All 42 generated-file hashes in the integration
  receipt match current files. Checked local Markdown links in the nine active
  entry documents: none missing. Raw preparation/supplier/route sources remain
  ignored intermediates; substantive observations and dispositions are retained
  in the durable ledger and named prior review/integration artifacts.

The active top-level records correctly distinguish the current `7355ae1a` PCB
from `0ad0135c`, the original AVA board and earlier R10 circuits. They do not
transfer an earlier clean pair, claim owner acceptance/order, or convert
simulation/CAD into physical/firmware qualification. AUD-2, AUD-10, GAP-3, the
single-switch amendment and the two-bank/always-on/SD changes retain their scoped
applicability. The corrected PC14 source withdraws the old 2.9 mA maximum;
3.33 V / 990 ohm independently gives 3.363636 mA, with dynamics still unmeasured.

## Coverage limits

No build, full check.sh, native CLI, GUI, Git action, other-worktree write or CAD
mutation was performed. The target commit is the immutable task-packet identity;
the exact board hash and current generated artifacts were checked directly.
The first two scratch probe attempts had local Python fixture errors and were
corrected before the successful complete run; neither was treated as a pass.
KiCad API initialization emits its known nonfatal wx/image-handler messages.

ST whole-PDF downloads timed out or exceeded the web extraction limit. Official
indexed/extracted text supplied pin/AF/loader evidence. A complete fresh rendered
LSM6 axis-figure inspection was unavailable; native pose/pad-1 consistency was
checked, and the retained signed map still requires the specified physical sign
test. No new axis result is inferred from an unseen image. No supplier quote,
new stock query, simulation sweep, firmware timing, physical/electrical/thermal,
RF/ESD, harness/retention, coating, fit or first-article qualification is claimed.

The JSON companion retains compact measured results, checks and exact source
hashes. Existing canonical files remained frozen; only these two assigned reports
and ignored scratch probes were written.
