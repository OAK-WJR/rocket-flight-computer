# R11 stage D: post stage, fab package, cost and stock (2026-11-03)

Follows stageC5.md. Decisions D-R11-64 … D-R11-72 in `R11_DECISIONS.md`. Nothing is committed or ordered; the R11
board and its fab package are **not** staged in git (D-R11-71). Evidence labels as AGENTS §2.5. Coordinates are board
mm (x east, y forward from the aft edge, KiCad's y).

## 1. Result in one paragraph

`m3_design/r11_build.sh` now ends with the post stage (`m3_design/r11_post.py`, from the frozen table
`m3_design/r11_legends.tsv`) and the fab package (`m3_design/r11_fab.sh`). Built twice: SHA-256
`d799a0b6c33f4b98e0e65a6cec5745a3d2c8f159737ef6800e8809e52fb358cf` both times (Measured). On it: DRC 0 violations, 0 unconnected, 0 schematic parity, ERC 0; check_r11 every rule
OK except **K-legends (22 findings)**; route_check `--profile r11` 0 failing, 2 allowlisted, 0 stale; the R11 fab package
binds and passes its three content checks; `tools/test_r11_check.py` 43 tests pass with `R11_BOARD` set and
`R11_BOARD_REQUIRED=1` (Measured). `tools/check.sh` would still fail on the R11 section at two steps owned by other
lanes: the metadata audit (21 contradictory `LCSC Part` fields from stage A, section 5) and K-legends' 22 legends with no
legal spot on this placement (section 3). Parts plus feeder fees are $79.73 per board at 5 boards against the $84.41
cap (live JLC data 2026-11-03T20:48:00Z); U9, U4 and U2 are short at JLC (section 7).

## 2. Post stage (D-R11-65)

* **No search in the build.** `m3_design/r11_legends_aid.py` (not run by the build) searched the routed board once
  (`b7e2decb…`, the stage C5 board) with R10's post-stage helpers on R11 data and froze every placement into
  `m3_design/r11_legends.tsv`: 490 rows (25 board texts, 11 pin-1 dots, 216 designators, 216 Fab references,
  22 open rows), positions in integer nanometres plus each item's expected ink box. A second aid run wrote the same file
  byte for byte (Measured, `cmp`).
* **`r11_post.py`** fills every zone, takes R8's digest of copper / zones / fills / pads / footprint positions, deletes
  board silkscreen, hides every field, moves the part-number fields (LCSC, LCSC Part, Manufacturer, Manufacturer Part,
  KiLib_Generator) to the Fab layer of their face, hidden (AGENTS §3), applies the table, sets the title-block revision
  M3-ASSY-R11, fills again (the digest must match) and saves. Its contract fails the build on: any applied ink box more
  than 0.002 mm from the table's, a text or designator under 1.0 mm / 0.15 mm, any silkscreen it draws nearer than
  0.15 mm to a mask opening, a pin-1 mark not nearer its own pad 1, anything in a support hardware circle, a K-fill
  finding, and any K-legends finding that is not one of the table's open rows (or an open row K-legends no longer
  reports).
* **Placed** (Measured on the built board): terminal legends J121 1:E1− / 2:E1+ (top, beside the pads, R10's meaning:
  E1− on OUT, E1+ on IGN), J1 1:BAT+ / 2:GND, J400 1:SW (top) / 2:SW (bottom), J122 1:S1 / 5:GND, J9 1:5V4 / 5:RXI /
  6:TXO, J410 / J420 / J440 1:4V8 and 4:RXI (every one strictly nearest its own pin, the aid's margin 0.1 mm over the
  gate's 0.01 mm); the words IGN, BAT, CAM, SWD and GPS (GPS inside J410's pin-row span); J2's rows 1:3V3 and 2:SWDIO;
  the revision M3-ASSY-R11 on B.Silkscreen; 11 pin-1 dots (U401 has no spot, its Fab mark only).
* **Designators:** 53 shown at 1.0 mm / 0.15 mm (15 top, 38 bottom; 8 top parts' under their part on the bottom),
  every SHOWN_REFS part but Q120 among them; **163 hidden**, kept on the Fab layer:
  C10 C100 C120 C123 C126 C127 C129 C13 C14 C15 C16 C17 C18 C19 C20 C21 C22 C23 C24 C26 C28 C29 C30 C31 C32 C400 C401
  C402 C403 C404 C405 C406 C407 C408 C410 C411 C420 C430 C431 C444 C460 C461 C5 C7 C8 C80 C82 C83 C86 C90 C91 C92 C93
  C94 C95 C96 C99 D123 D4 D400 D401 D410 D420 D421 D440 J430 L1 L400 LED1 LS120 Q120 Q122 R100 R101 R102 R103 R104
  R105 R11 R110 R119 R12 R120 R121 R122 R123 R126 R127 R128 R129 R13 R130 R131 R132 R133 R150 R151 R152 R153 R154 R155
  R156 R157 R162 R163 R164 R165 R166 R173 R175 R178 R180 R32 R33 R400 R401 R402 R403 R404 R405 R430 R431 R432 R440
  R450 R451 R460 R461 R462 R463 R464 R470 R471 R5 R60 R61 R64 R7 R81 R82 R83 R85 R86 R87 R88 R9 R90 R91 R92 TP120
  TP122 TP74 TP82 U10 U11 U12 U13 U2 U4 U400 U401 U402 U9.
* **Fab references:** one `${REFERENCE}` per footprint (55 footprints had none in the library and got one; none had
  two), inside its own Fab body where it fits, else beside it within 1.5 mm; sizes 0.8 mm (60), 0.6 (19), 0.5 (8),
  0.4 (105), 0.35 × 0.3 (13), 0.3 × 0.22 (11), stroke 0.15 × height. check_r10's Fab rules (R20-MFG-03, R21-GATE-05,
  R22-GATE-02, R23-GATE-04) report none (Measured: K-legends lists no Fab finding).
* **Zone fill** saved in the board: K-fill OK (Measured).
* **Note for the placement lane (not drawn by this stage):** U12's footprint pin-1 circle is 0.025 mm from U13 pad 5's
  mask opening, under JLC's 0.15 mm pad-to-silkscreen (r10_post's R3-MFG-02 test, Measured). DRC does not flag it
  (KiCad tests overlap only) and JLC clips silkscreen at openings (Inference from R10's `--subtract-soldermask` export);
  the post stage prints it as a NOTE instead of failing.

## 3. K-legends on R11: what cannot be placed (D-R11-66)

K-legends inherits R10's legend set: an individual pin legend strictly nearest every contact of J121, J1, J400,
J122, J9, J410, J420, J440 (R10's DB125 rule, D-AVA-01), the words, J2's SWD table, J122's harness note, and
SHOWN_REFS visible. On this placement 22 of them have **no legal spot on either face** (the 0.155 mm silkscreen gap to
pads, vias, holes, mask openings and other silkscreen, off package bodies and support hardware, 0.6 mm inside the
edge; Measured by the aid's search):

| Open item | Measured basis |
|---|---|
| Middle GH contacts J122.2–.4, J9.2–.4, J410.2–.3, J420.2–.3, J440.2–.3 | A 1.0 mm legend nearest its own contact on a 1.25 mm pitch must sit in a column about 1.15 mm wide (ink) and 4.3 mm long within about 1.7 mm of the contact (beyond that a 90° legend's bounding box, 0.848 mm half width, is no longer 0.01 mm nearer its own contact). Searched over ±8 mm on both faces before any other legend was placed: **no spot for any of these 12 contacts** (Measured). Behind J410.2, for example, the F.Cu column holds a GND via (21.60–22.05, 43.48–43.93), R32.2 (22.29–22.85, 42.03–42.57), LED1's body and C7's pads; on B.Cu C411's body spans x 19.05–22.34 under the connector. With every via removed (a test only), 9 of the 12 still have none (J9.3, J9.4 and J410.2 would get a bottom spot). |
| Words SERVO, RADIO, AUX, SWITCH | no spot within 12 mm meeting check_r10's tie and centre-margin rules (RADIO / AUX also the pin-row span) |
| J2 rows 3:NRST, 4:SWCLK, 5:GND, 6:NC; note `SERVO + FROM HARNESS` | no spot within 12 mm |
| Q120's designator (SHOWN_REFS) | no spot within 9 mm nearer Q120's courtyard than any other on either face, even on a board with no other silkscreen (Measured) |

A pin table per GH port (R7–R9's keyed-GH convention, `J410 1:4V8 2:GND` / `J410 3:TXO 4:RXI`) was also tried as a
test (J400 included as a GH port): 11 of 13 rows had no spot within 12 mm (6 even with every via removed). So the shortfall is silkscreen room on a
46 × 50 mm board with 216 parts and 394 vias, not the legend format (Measured). The 22 findings stay K-legends failures
in `tools/check.sh`; resolving them needs a placement change (free columns behind the GH contacts, room at J2 and Q120)
or an owner decision on R11's legend set (a check_r11 rule change). Neither is in this lane.

## 4. Gate corrections in check_r11 K-legends (D-R11-64)

Three places where K-legends encoded R10 rather than a rule, each now R11 data with a seeded test
(`tools/test_r11_check.py` R11Legends, 3 tests):
* `TERMINAL_PINS_R11`: J9's six GH contacts (1–2 5V4, 3–4 GND, 5 RXI, 6 TXO; D-R11-05). R10's four-pin list would have
  required `3:RXI` at J9.3, which is GND on R11.
* The revision: `check_r10.pinned_texts` binds R10's PINNED_TEXTS as a default argument and names M3-ASSY-R10 as the
  only revision, so check_r11's patch of the module constant never took effect; `pinned_texts_r11` requires exactly one
  M3-ASSY-R11 on B.Silkscreen and no other revision legend.
* The GPS / RADIO / AUX span: R10 requires the word inside its terminal's courtyard span along the pin row, coded as y
  (R10's rows run along y); R11's GH rows run along x, so `word_spans_r11` takes the span on each connector's own
  pin-row axis (the axis along which its numbered pads spread), with R10's 0.5 mm margin.
No rule was loosened: every R10 check still runs, with R11's pins, revision and axis.

## 5. Metadata audit: contradictory part-number fields (stage A, not changed here; D-R11-70)

`quality_audit/verify_board.py` (check.sh's "metadata / 3D model audit") fails the R11 board: **21 parts** carry an
`LCSC Part` field with R10's code beside the R11 `LCSC` code (AGENTS §3: no second, contradictory part-number field):
C83, C90, C93, R80, R81, R84, R85, R86, R87, R88, R89, R90, R91, R100, R101, R102, R103, R110, R162, R165, R167 (e.g.
R85 `LCSC` C29381, `LCSC Part` C137691). Present on the routed board before the post stage (Measured on `b7e2decb…`);
the fields come from the R11 sheets (`r11_sch.py` updates LCSC / Manufacturer / Manufacturer Part on a changed part,
line 350, but not `LCSC Part`). DRC, parity and ERC are clean. The fix belongs to stage A.

## 6. Fab package (D-R11-67, D-R11-68)

R10's `export_fab.py`, `jlc_orient.py`, `jlc_corrections.json`, `jlc_easyeda/pads.json` and `fab_manifest.py` are bound
inputs of R10's frozen package and are unchanged. R11 adds:
* `tools/jlc_easyeda/pads_r11.json` (R10's file plus 13 codes fetched 2026-11-03 by `tools/jlc_easyeda_r11.py` from the
  JLCEDA / EasyEDA Official Library, https://lceda.cn/, https://easyeda.com/: C964146 TFBGA-100, C189893 / C189895 /
  C189896 / C133065 GH 2 / 4 / 5 / 6, and eight 0402 resistor codes; C705636 has no EasyEDA record, so it takes the
  verified R0402 donor's correction as R10's C861313 does);
* `tools/jlc_orient_r11.py` and `tools/export_fab_r11.py`: R10's sources executed with asserted string replacements
  (R11's corrections file, the six copper layers, R11's GH fixing-tab numbers: SM02B 4 / 3, SM04B 6 / 5, SM05B 7 / 6,
  SM06B 7 / 8 from EasyEDA's pads);
* `tools/jlc_corrections_r11.json` (every R11 code OK; U1's TFBGA θ 90°, residual 0.000 mm over 100 balls; the GH
  ports θ 0, offset +0.25 mm, residual ≤ 0.075 mm);
* `tools/fab_manifest_r11.py`: these four files are inputs of the binding, and its content checks run check_r11 S-4 and
  `jlc_orient_r11.py --verify-cpl` on `pads_r11.json`.

`m3_design/r11_fab.sh` output on the built board (Measured): Gerber zip of 16 files (F / In1 / In2 / In3 / In4 / B
copper, both paste, silkscreen and mask, Edge.Cuts, PTH and NPTH drill, job file); JLC BOM 75 lines, 204 placed parts;
CPL 81 top + 118 bottom rows rebuilt from JLC footprints, worst pad residual 0.491 mm (C3013496 R2512 land, as R10),
5 placement-only rows (R150–R153, R400); paste 348 top / 319 bottom flashes on as many pasted pads; owner BOM C84 (hand
fitted, as R10); S-4 OK; manifest bound. Hashes: see section 8.

## 7. Cost and stock (D-R11-69)

Live public JLC data, read-only, for **5 boards** (Measured; `m3_design/r11/fab/cost_check.json` 2026-11-03T20:48:00Z,
`stock_check.json` 2026-11-03T20:47:10Z, both bound to the BOM / CPL hashes in section 8):
* **Parts $56.78 + feeder 75 codes × $1.53 / 5 = $79.73 per board** against the $84.41 cap: **$4.68 under** (R10 was
  $85.26, $0.85 over). 76 unique codes (47 Extended / 29 Basic by the stock check; the cost tool counts 46 Extended
  among the 75 charged codes), C84 owner-fitted ($0.203 per board, no fee).
* JLC fixed fees (standard PCBA, two sides: setup, stencil, fixture) **$83.96 per order = $16.79 per board** at 5, plus
  a $14.93 handling fee JLC may add; PCB, rails and shipping are outside the target.
* With JLC's minimum purchases (U9 7, U2 8): $58.02 per board ordered.
* **Stock: fails on three lines** (orderable = min(stockCount, canPresaleNumber), R20-BOM-01, an Inference about JLC's
  field): **U9** C3662793 TPS259470 stock 18, orderable −93 (need 5, minimum purchase 7); **U4** C51931514 ISM6HG256X
  stock 4, orderable −3 (need 5); **U2** C780769 stock 86, orderable −360 (need 8 at the minimum purchase). U4 and U9
  were short on R10 too; U2 is new. As R10 (ORDERING §8.1): confirm in the JLC cart on order day, else consign.
Prices and stock move daily; re-run `FAB_NET=1 m3_design/r11_fab.sh` before ordering.

## 8. Hashes (Measured)

| File | SHA-256 |
|---|---|
| m3_design/r11/m3.kicad_pcb | d799a0b6c33f4b98e0e65a6cec5745a3d2c8f159737ef6800e8809e52fb358cf |
| m3_design/r11_legends.tsv | 2b8226f658d05de7aed65e624d769f1dac0d8fe532ab6129b84cfef2b1769fed |
| m3_design/r11/fab/cost_check.json | 2ebcce57791034c2a7bd81e324a59b0d495b9015d403806b4382632c3d15716d |
| m3_design/r11/fab/m3_assembly_bottom.pdf | 3653e505a5a68ade1c27bb742827f6cc4c47873fccb232d947bbf91447f252b4 |
| m3_design/r11/fab/m3_assembly_top.pdf | 08aa8ae8a4d2dffe2d194bf74d7896d6d8eb327b7e38f61ee70735fadbdbb71f |
| m3_design/r11/fab/m3_bom_jlc.csv | 90310a4ef51af42bd425507460ed1c4af12fe651b87350d5ab0c99869327e616 |
| m3_design/r11/fab/m3_bom_owner.csv | c48868b32f2680376e73c4ea93c98df8efd6df4cad909c83e64a7ee56b74c2c0 |
| m3_design/r11/fab/m3_cpl_jlc.csv | dcb1e3a88520ed8a2239dbbeda9b2c09a91616b78602ecceec89d15f18bfbd38 |
| m3_design/r11/fab/m3_fab_manifest.json | e0123aa96c2600274e385a6850ee5299625eaee8e431b439087a0f1fc375eaac |
| m3_design/r11/fab/m3_gerber.zip | 4e0d07c5b99f1fece46b6805ce1409c89d61f99beef3208e99a69c7bab6aa2dd |
| m3_design/r11/fab/stock_check.json | b0d101a1bbbf8a956e6a13aa5cefb79399ca3f91700d2d1451c41fd09c8e4ace |

## 9. Not done / open

* `tools/check.sh` with the R11 board untracked (R10 gate and every self-test): exit 0 (Measured, 2026-11-03).
* Re-running after a copper or placement change: rerun `m3_design/r11_legends_aid.py` on the new routed board to
  refreeze the table; `r11_post.py` fails closed when an applied item no longer matches the board.
* `tools/check.sh` does not exit 0 with the R11 board tracked: the audit (section 5) and K-legends (section 3). The
  board and fab package are therefore not staged (D-R11-71).
* Plate model, JLC DFM on the panel and tabs (D-R11-12), first-article checks: not run.

**Fix pass (stageD2.md, D-R11-78 … -84):** the audit (section 5) and the 22 K-legends findings (section 3) are resolved
on board `5f1a7e1d…` (LCSC Part follows LCSC; SWITCH and Q120 placed; the R11 legend set, owner acceptance pending); the
board and fab package are staged. The hashes in section 8 are the stage D board's.
