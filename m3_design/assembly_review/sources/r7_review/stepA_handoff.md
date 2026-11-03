# R7 step A → step B handoff (board placement and routing)

Step A is done in the worktree, uncommitted (branch `m3-assy-r7`, base `3b215ba`). It covers the
schematic, the libraries and the part data. The board `m3.kicad_pcb` is untouched: it is still R6.
The record is `docs/M3_R7.md` §"R7 schematic". Read it first for the parts table, the pin contract,
the bias-limiter numbers and the cost.

## 1. State you start from

- **Native ERC 0.** `kicad-cli sch erc --severity-all` on `m3.kicad_sch`.
- **`tools/check.sh` stops at schematic parity, as expected.** DRC 0, unconnected 0, ERC 0, parity 92:
  - 38 `missing_footprint`: the new refs;
  - 37 `extra_footprint`: the removed R6 refs;
  - 17 `net_conflict`: U1 pads 31, 45, 51–57, 61 and 63–69.
- **Scripts, in order, both idempotent:**
  1. `<KiCad python3> -I m3_design/r7_parts.py` (library; `--check` verifies it is up to date);
  2. `python3 m3_design/r7_sch.py --netlist` (schematic, plus `schematic.net.xml`).
- **`r7_sch.py` exports `RF_PARTS` and `RF_MCU_PINS`.** Each `RF_PARTS` entry holds ref → lib_id, value,
  footprint, fields, pin→net and kind. These are the board builder's input, the way `TLM_PARTS` was
  for R6.
- **The netlist carries every attribute the board needs:**
  - footprint IDs and fields: LCSC, Manufacturer, Manufacturer Part, Datasheet; `JLC_Assembly` on
    J30/J31;
  - for the DNP parts, the `dnp`, `exclude_from_bom` and `exclude_from_pos_files` properties.

## 2. Removed refs: delete the footprints and their copper

- **The 37 refs:** J130, J131, U14, U15, U16, L4, TP130, D130, D131, C170–C180 and R190–R206.
- **Their nets:** TLM_*, RADIO_M0/M1/RXD/TXD/AUX(_MCU), RADIO_TX/RX_MCU, GPS_* and TLM_5V_REG.
  - Pass 1 counted 583 track segments and 105 vias on them.
  - Do not let a generic "remove dangling copper" pass touch other nets.
- **Shared nets keep their other copper:** 3V3, GND and RAW_PROTECTED.
- **U1 pads 31, 66, 67, 68 and 69 become unconnected.** Delete their fan-out copper.

## 3. New refs, footprints and side constraints

All footprints are in `kilib/rocket.pretty` and every one has a model in `kilib/rocket.3dshapes`. The
new models are envelope boxes.

| Ref(s) | Footprint | Side / placement constraint |
|---|---|---|
| U30 MAX-F10S | `M3_MAX_F10S_LCC18` | **Top only.** u-blox requires a single final upright reflow (IM §5): the top side must be JLC's last reflow. The courtyard includes the 0.6 mm de-paneling tab on both 9.7 mm edges and the 12.5 mm T-paste span. Pin 1 is top-left (pins 1–9 down the left side) |
| U31 E22-900MM22S | `M3_E22_900MM22S` | **Top only.** Pin 1 is at the left column, top (counter-clockwise) |
| J30 (GNSS), J31 (radio) | `M3_SMA_KH_KE8_EDGE` | Front footprint whose local y = 0 must lie **on the aft board edge**, with the body toward −y. See §4 |
| D30, D31 | `M3_TSLP_2_20` | On the RF line right at each jack: pad 1 to the line, pad 2 to GND |
| L30 | `M3_LQG15_0402` | On the GNSS line: the bias tap |
| FB30, FB31 | `M3_BLM18K_0603` | Next to each module's supply pin; 3V3 enters here |
| C303, C305, C313, C314 | `C0402` | **DNP** shunts: one pad on the RF line, the other into the coplanar ground |
| R304, R316 | `R0402` | Series link in each RF line, fitted |
| C300, C301 / C310, C311, C312 | `C0603`, `C0402` / `C0805`, `C0402`, `C0402` | C301 at U30 pins 7/8; C310–C312 at U31 pin 1 |
| R300 | `R_0603_1608Metric` | Bias-limiter sense |
| Q30, Q31, Q32 | `SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR` | Limiter. Pass-1 layout proposes B.Cu under U30's west half, with vias beside pins 13/14 |
| R301, R302, R303, R305, R306, R307, R310–R315 | `R0402` | Series-resistor placement: R306 at U1 (PC6 drives); R305 at U30 (TXD drives); R313 and R315 at U1; R314 at U31 (MISO drives) |
| TP30 | `M3_TestPad_1.5` | Bare pad on GNSS_SAFEBOOT_N. Treat it like the other TPs: exclude it from the BOM and position files, and give it a 1.0 mm local clearance |
| #FLG08, #FLG09 | — | Schematic only: power flags for 3V3_GNSS and 3V3_RADIO |

- **Pass-1 floorplan:** `pass1_layout.md` §3.3. The board is 46 × 118 mm, the RF strip is at the aft end,
  and everything existing moves +18 mm in y. GNSS jack at x 12.85, radio jack at x 31.54; U30 on the
  left, U31 on the right.
- **F10 needs ≥ 12 mm between the jacks, centre to centre.**

## 4. Special rules

- **SMA jacks J30 and J31:**
  - **No paste**: the pads carry no F.Paste or B.Paste. JLC hand-fits the jacks in its through-hole
    step after reflow (`JLC_Assembly` field; `export_fab` puts it in the BOM Assembly column).
  - Pads 1, 2 and 5 are on F.Cu; legs 3 and 4 are on B.Cu. All are 1.2 × 4.2 mm, from 0.2 to 4.4 mm
    inside the edge.
  - **Edge clearance:** the board rule is `min_copper_edge_clearance 0.5`, and a violation is a DRC
    error. Add a footprint-scoped 0.2 mm edge-clearance rule for J30/J31 in `m3.kicad_dru`. Then update
    `DRU_SHA` in `m3_design/check_actuators.py` after review.
  - **Overhang:** the body sticks out 9.5 mm beyond the aft edge (flange 1.5 + thread 8), the axis is
    0.45 mm above the top face, and the flange reaches about 1.3 mm below the bottom face. Rails go on
    the long edges only. JLC's DFM will query the body outside the outline: confirm it is deliberate.
  - **The F.CrtYd and B.CrtYd courtyards extend beyond Edge.Cuts.** That is intended.
  - **`tools/fit_check.py` needs an SMA mated-plug envelope.** Use pass-1 `pass1_layout.md` §6.4. Replace
    the J130/J131 SH entries in MATED / REQUIRED_MATED.
  - **Second source:** the BAT WIRELESS C496550 fits the same land, but its EasyEDA numbering swaps
    legs 1 and 2. `r7_parts_check.json` shows a CHECK for it, which is expected because it is not
    ordered.
- **DNP parts C303, C305, C313 and C314** need `FP_DNP | FP_EXCLUDE_FROM_BOM | FP_EXCLUDE_FROM_POS_FILES`.
  - `r6_pcb.synchronize()` only set the exclude flags for TP*/J2. Read the netlist's `dnp`,
    `exclude_from_bom` and `exclude_from_pos_files` properties, or KiCad's "Update PCB from Schematic"
    does it.
  - Schematic parity may compare these attributes.
  - They carry an empty LCSC field and no maker fields, which quality_audit allows for non-fitted parts.
    They have the C0402 model.
- **Keep-outs:**
  - Under U30: no signals on F.Cu or In1 (u-blox IM §4.4).
  - Under U31: no tracks or vias other than GND on any layer (EBYTE §4.1).
  - Put these in DRC rule areas or custom rules, so they are enforced and not just intended.
  - Keep RF parts ≥ 5 mm from U2/L1 (3V3 buck), the MCU, Y1, U3 and fast digital lines, and clear of the
    pyro block and igniter terminals (F10).
- **RF lines:**
  - 50 Ω GCPW on F.Cu over In1 GND. Pass 1 gives W 0.30 / G 0.25 mm for the JLC041611-7628 stackup
    (`pass1_layout.md` §5), so set the KiCad stackup to it.
  - Cut In1 out under each SMA centre pad (1.8 × 4.6 mm).
  - Place a GND via fence at ≤ 1.5 mm pitch, plus a strip-boundary fence.
  - Chain order from each jack:
    - GNSS: D30, L30 tap (C302 at its cold end), C303, R304, C305, RF_IN.
    - Radio: D31, C313, R316, C314, ANT.
- **Power:** 3V3 → FB30 → 3V3_GNSS, and 3V3 → FB31 → 3V3_RADIO. Keep the ferrites and bulk capacitors
  local to each module. The MAX-F10S allows ≤ 0.2 Ω of series resistance on VCC (FB30 is ≤ 0.05 Ω).

## 5. What step B must verify or update

- **`tools/jlc_orient.py`:** regenerate `tools/jlc_corrections.json` for the new LCSC|footprint pairs and
  compare the result with the expected theta and offset in `r7_parts_check.json`. Every pair is OK with a
  residual ≤ 0.235 mm. The SMA expects an offset of (0, −2.3) mm, because EasyEDA's pads are 5.0 mm long
  and centred differently.
- **Contracts and tools that still encode R6** (`pass1_requirements.md` §5.6 lists them line by line):
  - `tools/check_r6.py`: J130/J131 FOOTPRINTS, CONNECTORS and SIGNALS; the TLM/U14–U16 block; the
    110 mm limit and the 80–90 mm note; the edge-block rule; the legends. Also add U1.31/66/67/68/69 to
    the NC list.
  - `m3_design/check_actuators.py`: the PINNED J130/J131/U14/U15/U16/R195/D130/D131 entries and the TLM
    rules. PYRO_BLOCK is in absolute coordinates, so shift it by +18 mm if the board is translated.
    DRU_SHA too. The pyro sentinels are still without a net.
  - `tools/fit_check.py`: the SMA envelope, RETENTION_HOLES (+18 mm), the 120 mm limit, the SIDE_ENTRY
    list.
  - `tools/jlc_cost.py` and `tools/check_procurement.py`: the targets become 126.41 / 52
    (REQUIREMENTS M3).
  - Tests: `test_fit_check.py`, `test_r6_check.py`, `test_procurement.py`, and the J130/C160393 fixture
    in `test_fab_validation.py` (`test_connector_mechanical_tabs_are_independently_checked`).
  - `tools/jlc_orient.py` MECHANICAL still names the SH footprints. They are stale but harmless.
- **Fab package:** run `export_fab.py`.
  - It must print `not fitted (DNP placeholders, …): C303, C305, C313, C314` and `owner-fitted: none`.
  - Then run `jlc_stock.py` and `jlc_cost.py` with a supplier snapshot no more than 24 h old.
  - Step A's snapshot of all 92 R7 codes is from 2026-10-15 21:53Z.
  - Expected result: 92 codes, **52 extended (the limit, zero margin)**, and about $110.95 per board
    against the $126.41 cap.
  - U4 (C26633007) is still short: stock 0, so use the consignment route. This is not an R7 item.
- **Stock:** the MAX-F10S has 18 in stock with ATP 9 for the 5 needed. Reserve it (JLC parts pre-order)
  when ordering.
- **Silkscreen:** "GPS" / "915" legends at J30/J31, and the board revision legend M3-ASSY-R7. Designator
  rules are as in AGENTS §3.
- **Firmware binding:** a new R7 binding is needed (AGENTS §3; `pass1_electrical.md` §5.4). No firmware
  was written.

## 6. Not finished, inferred, or open in step A

- **E22 land:** EBYTE publishes no land, only the drawing. It is derived (pad + 0.05 / 0.70 toe; an
  Inference) and identical to JLC/EasyEDA.
- **TSLP-2-20 mask:** Infineon draws one mask opening around both pads. Here each pad has its own opening
  with a 0.30 mm web, because the board forbids bridged apertures. The effect on assembly is an Inference.
- **MAX-F10S paste:** u-blox's T-shape is specified for a 150 µm stencil, and ORDERING prefers 0.10 mm,
  which gives about 67 % of u-blox's paste volume (Inference). Decide the stencil, or accept it, in
  ORDERING.
- **Bias limiter:** the short-circuit current (≤ 46 mA cold, 27–46 mA over −20…+85 °C), Q32's VEB, the
  required collector current and the loop stability are Inferences. VCC_RF has only a typical value
  (VCC − 0.1 V), so the 2.93 V at 15 mA is typical. Bench-test: short the SMA with the receiver
  running.
- **R311 2.0 kΩ:** it holds NRST low against the SX1262's internal pull-up (pass 1: 0.13 V). Whether the
  E22 module adds its own NRST pull-up is unknown (Inference). Measure NRST with PD9 high-Z.
- **RF switch isolation:** with TXEN = RXEN = 0 the E22's internal RF switch state is assumed (pass 1).
- **REQUIREMENTS text:** pass-1 corrections were not edited, because step A covered the schematic and
  data only:
  - F8 still mentions the SH7/SH4 edge block;
  - F10 still says −12 dBm / 34 dB (pass 1: −17 dBm, ≥ 39.3 dB);
  - the R6 checkpoint logs at the end;
  - ORDERING.md, STATUS.md, the AGENTS table, the FMEA, and the parent VEHICLE.md stack row.
- **`sheets/*.svg|png` renders were not regenerated.** They are stale since R3. `schematic.net.xml` was
  regenerated.
- **Pre-existing, not R7:** 22 R6 symbols carry maker strings that differ from `tools/verified_part_metadata.json` only in naming (for example "Murata" vs "Murata Electronics", "Yageo" vs "YAGEO" on L3, C21397/C85980, R70–R72, U3 and others). quality_audit does not flag these. Every new R7 symbol matches the catalog exactly, and both catalogs list the R7 references.
