# M3-ASSY-R2 — actuator merge (current)

2026-09-25. R2 adds the actuator power switch, dual independently fused pyro channels with a complete arming break, four servo outputs, the launch pull-pin and the buzzer to R1, on a 46 × 238 mm board (203 positions, 178 fitted parts, 25 test pads, 14 sheets). Design rationale, datasheet evidence, routing method and the open verification list: [docs/M3_ACTUATOR_MERGE.md](../../docs/M3_ACTUATOR_MERGE.md). `top.png`, `bottom.png`, `drc.json`, `erc.json`, `schematic.net.xml` and `sheets/` are regenerated for R2. The R1 evidence files (`verification_assembly.json`, `visual_review.json`, `bom_review.json`, `visual_inputs.json`) are kept as the R1 record; they are bound to the R1 hash and do not describe R2. Manufacturing files: `fab/` (from `tools/export_fab.py`).

---

# M3-ASSY-R1 assembly correction review

2026-09-08. This revision is still a bench candidate: one 46 × 186 mm four-layer board for ordinary power / acquisition / logging / camera interface / bench diagnostics. 135 footprint positions: 115 nominally fitted parts and 20 test points. It does not implement every rocket function in the requirements; the full gap list is in [the requirement status](../../STATUS.md).

Open `m3.kicad_pro`. PCB SHA256: `e432d3436d5029de0a74a4b0ebcd02ec092dedf6d4252ce310f7be301558627f`.

## Assembly discrepancies confirmed and corrected

| Ref | Purchased identity and evidence | Handling in this revision |
|---|---|---|
| LED1 | NATIONSTAR NCD0805R1, LCSC C84256; maker drawing p. 2, cathode = pin 1 of this drawing | Dedicated footprint M3_NCD0805R1_K1; 0.8 × 1.2 mm lands at ±0.85 mm centres, 0.90 mm inner gap; its own cathode silkscreen |
| LED2 | KENTO KT-0805Y, LCSC C2296; maker drawing p. 2 states pin 1 positive, pin 2 negative | Dedicated footprint M3_KT0805Y_A1; 1.0 × 1.4 mm lands at ±0.95 mm centres, 0.90 mm inner gap; cathode on the other end |
| U3 | Winbond W25Q128JVSIQ, LCSC C97521; Rev G package drawing, PDF p. 68 / printed p. 67 | The 208 mil SOIC choice is correct; maker and part-number fields completed; not replaced with a narrow-body package |

The old generic LED land had centres at ±1.10 mm and 1.0 × 1.25 mm pads, matching neither maker's recommended drawing. The two LEDs' pin numbers and nets were not swapped; their genuinely different cathode numbering is expressed through different footprints.

All three references use consistent Manufacturer / Manufacturer Part / LCSC fields in the PCB, schematic and per-reference BOM. All 2201 original tracks and vias, every other part's pads and position, net assignments and pour boundaries are unchanged. The only copper-shape change is the four LED pads, with fills regenerated. Two old revision labels on the top silkscreen were changed to ASSY-R1 so a physical board cannot be confused with the host diagnostic revision.

## What the 3D models mean

The LEDs use their maximum-size envelopes: LED1 2.1 × 1.3 × 0.7 mm; LED2 2.1 × 1.35 × 0.95 mm. A green bar marks the cathode; the mesh splits the body and bar into adjacent solids so the bar doesn't coincide with the top face and vanish in native renders. They are locally created orientation and size envelopes, **not maker STEP files and not physical assembly verification**. All other retained models have the same evidence boundary.

`top.png` and `bottom.png` are native renders of the saved PCB; `led_native_closeup.png` is a crop of the top render; `led_detail.png` is read back from the saved pads to check local coordinates and polarity. `visual_review.json` records the hashes of the images actually reviewed.

## Checks and firmware

`verification_assembly.json` binds the saved PCB, the ten schematic sheets, the maker PDFs, the library files and the models. Native all-severity DRC, unconnected items, schematic parity and ERC are all zero; nothing passed by ignoring violations. There were also negative tests for wrong pads, wrong polarity, wrong model rotation, wrong part number, old silkscreen labels and copper changes.

[Diagnostic firmware v0.8.1](../../m3_firmware/ASSEMBLY_DIAGNOSTICS.md) was rebuilt against this revision's exact PCB hash; its production C and headers are unchanged from PDIAG v0.8. Both share wire encoding v8, but the host tools verify board ID and build identity separately, so an old image cannot pass as compatible with the new board.

Reference Gerbers, drill files, the 115 fitted positions and the BOM were produced with the review. Purchasing stock, rotation conventions for assembly, the remaining footprints, harness mounting, real electrical dynamics and whole-board function are not yet accepted, so this is not a manufacturing release package.

## Maker documents

- [NATIONSTAR NCD0805R1 datasheet, p. 2](https://datasheet.lcsc.com/datasheet/pdf/e3e35db60c068efe42b02d21fe498cf3.pdf?productCode=C84256): envelope and recommended land; [purchased identity C84256](https://www.lcsc.com/product-detail/C84256.html).
- [KENTO KT-0805Y datasheet, p. 2, 2018-12-06](https://datasheet.lcsc.com/datasheet/pdf/3f6a14f9ea2fc39f6e05d2ab0fa53e2b.pdf?productCode=C2296): pin polarity numbering, envelope and recommended land; [purchased identity C2296](https://www.lcsc.com/product-detail/C2296.html).
- [Winbond W25Q128JV Rev G, 2019-04-08](https://www.winbond.com/resource-files/w25q128jv%20revg%2004082019%20plus.pdf): 208 mil package drawing and ordering codes; [purchased identity C97521](https://www.lcsc.com/product-detail/C97521.html).

The PDFs themselves are not in this repository (download them from the links); their SHA256 hashes are in `sources.json`, and the extracted drawing images are in `sources/`. These drawings were used for this dimension / polarity check; they are not a current stock check, a supply-chain lock or a full electrical re-qualification of the parts.
