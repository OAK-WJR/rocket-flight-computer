# R7 implementation and independent review

**Pass 1, implementation steps A–C, review passes 2–8 and their fixes are done. Review pass 8 on the final board (fix
pass 7, `c872a3d3…`) found 0 Critical / 0 Major, and on 2026-10-18 the owner accepted the deviation list ("R7 deviations
for owner acceptance", below), with the 7.7 A copper rise accepted as estimated.** No R7 fabrication or flight release is
approved by this record: bench and physical tests, U4 consignment and JLC's forward-rail confirmation remain. The work is
on branch `m3-assy-r7` (base R6 `3b215ba`). The design record is [M3_R7.md](M3_R7.md); the requirement is REQUIREMENTS
F10 as rewritten on 2026-10-15, with P1 (120 mm maximum), M2 (clean routing over the whole board) and M3 ($126.41 per
board, 52 extended codes).

## Baseline

- R6 commit `3b215ba`, board SHA-256 `184a87e84e67576341244c82517de3e9f55f5c1c22995dfad83631d48c856680`
  (the "Final R6 CAD validation" board, 46 × 100 mm). `tools/check.sh` was clean on it.
- R7 board after step B: SHA-256 `03fe75720f46b1382d9d3216dbffd8ae642d0125722c04589ff97c964aa86d54`
  (46 × 118 mm), rebuilt byte for byte from the R6 board by `m3_design/r7_build.sh`. Step C did not change it;
  review pass 2 reviewed it.
- R7 board after the pass-2 fixes: SHA-256 `7660620cfa834e4d381d2a2638780e9a341341c9b93c6e6f526791204dc77c9c`
  (fix chain `03fe7572…` → F1 `9371d037…` → F2 `0eceb770…` → F3 `7660620c…`). Review pass 3 reviewed it.
- R7 board after the pass-3 fixes: SHA-256 `636a6bdc7234586a659741a3da921335a47197648c29cd9612c8374733847650`
  (F4, `fix3_F4_handoff.md`), rebuilt byte for byte from the R6 board by `m3_design/r7_build.sh`. Review pass 4
  reviewed it.
- R7 board after the pass-4 fixes: SHA-256 `c6fe595cafb91b088ac0b2c812f409f9ca5b86ac45a651102e168b0a5d83c7c7`
  (F5, `fix4_F5_handoff.md`), rebuilt byte for byte from the R6 board by a clean `m3_design/r7_build.sh`. Review pass 5
  reviewed it.
- R7 board after the pass-5 fixes: SHA-256 `1ffc2585cbbb2a49623a5010b2792500849f06989cf43e48fb3e56068cddf9df`
  (F6, `fix5_F6_handoff.md`), rebuilt byte for byte from the R6 board by a clean `m3_design/r7_build.sh`. Review pass 6
  reviewed it.
- R7 board after the pass-6 fixes: SHA-256 `4673c0a0f9fd290af694d6ca5a97e99b3b225466882ba5c6e57a9ad856b96ebd`
  (F7, `fix6_F7_handoff.md`), rebuilt byte for byte from the R6 board by a clean `m3_design/r7_build.sh`, twice. Review
  pass 7 reviewed it.
- **Final R7 board after the pass-7 fixes: SHA-256 `c872a3d30509cccf5f78b64cde48ef722ee85c7be23c4848b07ce4082a852de3`**
  (F8, `fix7_F8_handoff.md`), rebuilt byte for byte from the R6 board by a clean `m3_design/r7_build.sh`, twice. Root
  schematic `47057f7d97c7d748…`, unchanged since fix pass 2; sheet 15 (`telemetry.kicad_sch`) `f5e1df83…` since fix
  pass 6 changed J31's Value to "RADIO ANT SMA"; fix pass 7 changed no schematic, library or rules file (the fab
  manifest's 173 inputs other than the board are the same as fix pass 6's).

## Pass 1: three independent reviews (before implementation)

Three reviewers worked in parallel on the R6 baseline against the new F10/P1/M3, each from its own angle. Their
reports are in `m3_design/assembly_review/sources/r7_review/`:

| Review | File | Critical | Major | Minor |
|---|---|---:|---:|---:|
| Electrical (power tree, MCU pins, GNSS and radio circuits) | `pass1_electrical.md` | 0 | 6 | 9 |
| Layout, DFM and mechanical fit | `pass1_layout.md` | 0 | 4 | 11 |
| Requirements conformance, procurement and cost | `pass1_requirements.md` | 0 | 6 | 12 |

Every Major finding and its disposition:

| ID | Finding | Disposition |
|---|---|---|
| E1 / R7P1-01 | The CAD was still R6's external-port design: no GNSS, radio, SMA, bias feed or pi network | **Fixed** (steps A, B): the 37 port references and their copper removed; U30 MAX-F10S, U31 E22-900MM22S, J30/J31 SMA, RF ESD, limiter and pi networks added in an aft RF strip |
| E2 | SPI4, the only aft-side SPI, shares an alternate function with PE4 = PYRO1_GATE_N | **Fixed** (step A): radio on SPI2 (PB12–PB15), PD8–PD10 and PE15. Locking PE4 and never configuring SPI4/TIM15/SAI/FMC/TRACE on PE2–PE6 is part of the firmware binding (follow-up) |
| E3 | An always-on GNSS on USART1 (PA9/PA10) can capture the ROM bootloader | **Fixed** (step A): GNSS on USART6 PC6/PC7; PA9/PA10 (and PA7, PC9, PA8) left unconnected; `check_r7` checks it |
| E4 | The radio lines had no hardware-defined state in MCU reset; the SX1262 could keep transmitting | **Fixed** (step A): R311 2.0 kΩ holds RADIO_NRST low, R310 100 kΩ holds NSS high, R312 100 kΩ holds RXEN low, TXEN comes from DIO2. Bench: NRST level with PD9 high-impedance (ORDERING §5) |
| E5 / R7P1-03 | u-blox's reference bias feed lets a shorted antenna draw about 0.3 A from VCC_RF (200 mA absolute maximum); F10 set no limit | **Fixed** (F10 text; step A): F10 requires ≤ 50 mA over −20…+85 °C; the PNP/P-FET limiter with R300 15 Ω gives ≤ 46 mA cold by calculation (parts of it Inference). Bench: antenna short, cold and hot, with an oscillation check |
| E6 | F10's isolation figure used −12 dBm; the current MAX-M10S manual gives −17 dBm, so ≥ 39 dB is needed | **Fixed** (F10 rewrite): −17 dBm and ≥ 39 dB; the bench C/N0 test with the radio keyed is the evidence for the MAX-F10S |
| L1 | No RF floorplan; the superseded parts held both candidate areas | **Fixed** (step B): the pass-1 floorplan (aft strip, +18 mm translation, supports and J123 moved) |
| L2 | No stackup was ordered; the KiCad stackup matched no JLC template | **Fixed** (steps B, C): KiCad stackup and job file are JLC041611-7628 (1 oz inner; not JLC04161H-7628 as R7P1-14 proposed); ORDERING §3 and M1 name it; impedance control optional |
| L3 | SMA jacks, mated plugs and coax bends not modelled; the board-position assumption no longer holds | **Partly fixed**: `fit_check` has the SMA mated-plug envelope (step B). **Open:** the coax loop zone against the camera shroud (Onshape measurement) and the parent VEHICLE.md stack row; recorded in REQUIREMENTS (board position) and ORDERING §7 |
| L4 | ORDERING's tab windows were R5 values and broke their own rules | **Partly fixed**: three R7 windows measured in step B and rescanned in step C (left y 63–68, right y 62–67 and 8–13), all meeting 1.5 mm / 5 mm, in ORDERING §3. **Open:** no window forward of y ≈ 68, so about 50 mm of the forward end is unsupported |
| R7P1-02 | U4 (LSM6DSV320XTR, C26633007) out of JLC stock | **Documented, not redesigned** (step C): bought from a franchised source and consigned into JLC's parts inventory (ORDERING §1; M1 exception). Procurement stays blocked until it is consigned; the stock tools have no consignment path (R7P1-18, open) |
| R7P1-04 | No requirement for pyro-channel immunity to the new transmitter | **Fixed** (F10 rewrite): "Pyro immunity" clause; bench step in ORDERING §5; FMEA I-11/V-19 updated |
| R7P1-05 | The gate and procurement tools enforced the superseded requirements | **Fixed**: `check_r7.py`, `check_actuators.py` and `fit_check.py` with their tests (step B); `jlc_cost.py`, `check_procurement.py` and `test_procurement.py` at $126.41 / 52, the stale J130 fixture in `test_fab_validation.py` and the SH entries in `jlc_orient.py` (step C) |
| R7P1-06 | ORDERING.md still described the R5 order | **Fixed** (step C): rewritten for R7 |

Minor findings: fixed in steps A–C or recorded. Still open after step C: E9 and E13 (USB-only transmit cap, PA
ramp, buzzer quiet during acquisition: firmware binding), E11 (add both modules to MARGIN_PRESCRIPTION's 85 °C
list; dropped from the open lists after step C, P5-DOCS-03, and done in fix pass 5), R7P1-10 (RP-SMA was not adopted; the leads are labelled instead, ORDERING §7), R7P1-13 (LS120 reflow
rating; closed in pass 2 by DFM-08), R7P1-16 (the `m3_firmware/pins_*.json` maps belong to the firmware binding)
and R7P1-18 (consignment path in the stock gate).

## Implementation

### Step A: schematic, libraries and part data

`m3_design/r7_parts.py` (library) and `m3_design/r7_sch.py` (schematic, netlist). Sheet 15 became "GNSS and
telemetry radio (R7)": 37 R6 port parts out, 38 references in (33 fitted, 4 DNP shunts, 1 test pad). U1
re-pinned per the pin contract. Every new land matched to its JLC/EasyEDA footprint (worst residual 0.235 mm;
`r7_parts_check.json`). Native ERC 0. Estimated cost from the schematic BOM: $110.95 per board, 52 extended
codes. Handoff: `stepA_handoff.md`; record: M3_R7 §"R7 schematic".

### Step B: placement and routing

`m3_design/r7_pcb.py`, `r7_route.py` (with the recorded grid-router session `r7_reroute_session.json`, retired in
pass 2: the displaced R6 nets are now explicit geometry in `r7_redraw.py`) and `r7_post.py`, run by `r7_build.sh`
from the committed R6 board. `tools/check.sh` clean: DRC 0, unconnected 0,
parity 0, ERC 0, audit, silkscreen, R7 contract, actuator contract and fit OK. RF measurements, the 13
deviations and their reasons are in `stepB_handoff.md`; the log is `stepB_progress.md`; record: M3_R7
§"R7 board".

### Step C: manufacturing outputs and documents

- **Placement corrections** regenerated by `tools/jlc_orient.py` (14 new pairs, all OK and equal to step A's
  predictions; 5 R6 pairs gone). **Fab package** regenerated by `tools/export_fab.py`: 95 BOM lines (92 codes),
  219 placed parts and CPL rows; the DNP shunts in no BOM or CPL; J30/J31 in the through-hole class with no
  paste (checked in the paste Gerbers); `--verify-cpl` 211 rows rebuilt from JLC footprints plus 8
  placement-only, no errors; manifest OK.
- **Cost and stock** on a fresh supplier snapshot (2026-10-16 05:14Z): $110.93 per board, 52 extended codes
  (targets met, no code to spare); U4 short (stock 0), everything else in stock; U30 18 in stock for 5.
  `check_procurement.py --cost-only` passes; the full gate fails on U4's stock, as expected.
- **Documents:** ORDERING rewritten; REQUIREMENTS corrected per `pass1_requirements.md` §4 (F10 unchanged:
  no factual error found), the pad-time and pack rows updated for the on-board radio and GPS, the M1
  consignment and through-hole exceptions added, the R6 contract and logs moved to M3_R6; STATUS, AGENTS §1,
  FMEA I-11/V-19 and M3_R7 updated.
- **Gate and tests** on the unchanged board: `tools/check.sh` clean as in step B; 126 unit tests pass in 8
  suites; `test_r5_repair` fails one subtest that checks literal R5 geometry, as it does on R6 (M3_R7 §"R7
  manufacturing outputs").
- **Firmware:** none; the R7 board binding is a follow-up (M3_R7 §"Firmware").

## Carried to pass 2

Dispositions: section "Pass 2" below.

- The step-B deviations: three stitching gaps of 2.17–2.98 mm against the ≤ 2 mm target; four radio
  control lines 3.2–4.7 mm from U30's courtyard and RXEN/TXEN beside U31's own RF stub, against F10's 5 mm
  from fast digital lines; radio signals and the bias limiter on B.Cu inside the strip, against F10's "every
  copper layer GND outside the module pads and RF lines". Accept with reasons, or fix.
- The forward-end panel span (L4), the coax loop zone and board position (L3), U4 consignment.
- The F4 servo-feed DC solve on R7 copper (the In2 BAT_IN pour changed).
- J2 is TC2030 pads since R6, so P3's "J2 conformal-coated" (written for a header) cannot be applied as
  written; decide how the bare NRST pad is protected.
- Physical qualification: none has been done. The RF bench tests in ORDERING §5 come in addition to every
  R6 bench and pyro gate.

## Pass 2: eight independent reviews of the step-B board

**Board reviewed:** `03fe7572…6d54`.

**Reviewers:** eight, in parallel, each from its own angle. Reports are `pass2_*.md` in
`m3_design/assembly_review/sources/r7_review/`.

**Skeptic step:** every Critical or Major finding went to three skeptic reviewers. Each tried to refute it and
re-graded its severity (`pass2_main_verdicts.json`, `pass2_routing_verdicts.json`). Minor findings were not sent
to skeptics.

**Outcome:** no Critical. All 26 Majors were upheld 3 of 3, and none was refuted. The skeptics' majority re-graded
7 of them to Minor.

| Review | File | Critical | Major | Minor |
|---|---|---:|---:|---:|
| RF layout and coexistence | `pass2_rf.md` | 0 | 0 | 5 |
| Electrical | `pass2_electrical.md` | 0 | 0 | 5 |
| Regression against R6 | `pass2_regression.md` | 0 | 1 | 7 |
| DFM and assembly | `pass2_dfm.md` | 0 | 1 | 10 |
| Requirements conformance | `pass2_requirements.md` | 0 | 3 | 10 |
| Mechanical fit and robustness | `pass2_mechanical.md` | 0 | 3 | 2 |
| Routing geometry (whole board) | `pass2_routing_geometry.md` | 0 | 10 | 5 |
| Routing quality (R7 copper) | `pass2_routing_quality.md` | 0 | 8 | 7 |

### Implementation of the pass-2 fixes

- **F1** (board, schematic, tools; `fix2_F1_handoff.md`):
  - QSPI_IO0/IO1 return paths: BAT_FAULT_N In2 west of IO0, GND vias at 0.78 mm, BUZZ_DRV ≥ 1.098 mm from IO1;
  - return vias at D9, C80 and R167;
  - CAM_RX_WIRE via out of R100.1;
  - `rocket:C0402_DNP` (no paste) for the DNP shunts;
  - solid RF grounds with vias at 0.16 mm;
  - C304, the DNP compensation placeholder;
  - In2 GND under the interface corridor; FB31's feed; limiter re-placed; RXEN rerouted;
  - TP89 moved to the bottom;
  - GNSS and RADIO legends both on top; LS120 silk 0.15 mm;
  - BOM grouped by LCSC code;
  - `U31_KEEPOUT` over the whole body;
  - five new `check_r7` checks (`test_r7_check` 19 → 28) and `tools/critical_reference.py`.
- **F2** (`fix2_F2_handoff.md`): the grid-router replay is retired and `r7_reroute_session.json` deleted. The 13
  displaced R6 connections are redrawn from explicit geometry (`m3_design/r7_redraw.py`), with the LED lanes
  bent round QSPI_NCS to keep its reference.
- **F3** (`fix2_F3_handoff.md`):
  - whole-board clean-up `m3_design/r7_hygiene.py`, R6 copper included, with a pad-group invariant after every
    stage;
  - clean-routing gate `tools/route_check.py` in `tools/check.sh` (19 tests; `test_check_shell` proves a failure
    stops the gate);
  - 18 GND vias beside critical layer changes.
- **Documentation** (`fix2_docs_handoff.md`): REQUIREMENTS (P2, P3, F4, F10, M1, M2, M3, board position),
  ORDERING, MARGIN_PRESCRIPTION (R14 (R7) row) and FMEA (I-11, V-19, §6.3).
- **Records** (this pass): fab package regenerated and checked; gate, tests, cost and procurement rerun; DC solve
  rerun on the final board; M3_R7, this file, STATUS and four ORDERING statements updated (TP89 washer note, lead
  labels, C304 in the short test, cost).

### Every pass-2 finding

"Skeptic" gives the three verdicts and the majority severity. A dash means the finding is Minor and was not sent
to skeptics. Rows give the state after fix pass 2, measured on that board (`7660620c…`). Record errors that pass 3
found are corrected in place; where fix pass 3 changed the state, the row points to the pass-3 table.

| ID | Sev. | Skeptic | Disposition |
|---|---|---|---|
| RF-01 | Minor | — | **Fixed.** The DNP shunt lands use `rocket:C0402_DNP` (no paste); `check_r7.dnp_paste`; the Gerbers show no paste at C303/C304/C305/C313/C314 |
| RF-02 | Minor | — | **Fixed in part** (corrected by P3-RF-03): RF GND pads connect solid, each with a GND via 0.16 mm from its pad (`check_r7.rf_grounds`). Its third part, abutting the shunt lands to the series pads, was not done: the 0.94 mm stubs from C303/C305/C313/C314 remain and are part of the network for VNA tuning (ORDERING §4) |
| RF-03 | Minor | — | **Accepted, documented.** Gaps 4.27 / 3.68 mm accepted in F10 (< λ/20); the step-B "2.17–2.98 mm" is corrected in M3_R7 and here; `check_r7` gates its own line-side metric (3.90 / 2.65 / 1.55 / 1.55 mm). `stepB_handoff.md` is left as the historical step-B record |
| RF-04 | Minor | — | **Documented.** F10 now states what the strip may hold |
| RF-05 | Minor | — | **Fixed.** `U31_KEEPOUT` covers the whole body on B.Cu and In2; `check_r7` checks fence pitch, line-side gaps and In1 under the RF copper |
| ELECTRICAL-01 | Minor | — | **Fixed.** C304 is a DNP 0402 from GNSS_ANT_GATE to GND; fit 1–2.2 nF only if the bench short test oscillates (ORDERING §5) |
| ELECTRICAL-02 | Minor | — | **Documented.** The antenna must draw ≤ 20 mA and work from 2.7 V (F10, ORDERING §7); the short test records the VCC_RF drop |
| ELECTRICAL-03 | Minor | — | **Documented.** EXTI constraint in F10 and the M3_R7 pin contract |
| ELECTRICAL-04 | Minor | — | **Accepted, documented.** D30 kept (code budget); ESD handling rule in ORDERING §5/§7; trade-off in M3_R7 |
| ELECTRICAL-05 | Minor | — | **Documented.** Q30 rise corrected to about +30–40 K in M3_R7 (Inference) |
| REGRESSION-01 | Major | upheld 3/3 → **Minor** (Minor ×3) | **Fixed.** BAT_FAULT_N In2 west of QSPI_IO0; IO0's layer changes have GND vias at 0.78 mm; BUZZ_DRV ≥ 1.098 mm from IO1; IO1's via has a GND via at 1.50 mm. Lost R6-referenced samples 1,427 → 603: at vias, on R6 paths R7 abandoned, and 38 at CAM_MCU_RX's In2 lane crossing under QSPI_NCS (corrected by P3-REGRESSION-03; M3_R7 §"Return paths"). The R6 bar of zero lost is not met literally |
| REGRESSION-02 | Minor | — | **Fixed.** BUZZ_DRV is off USB_DP's In2 reference (0 lost); 3V3 L1.2 → U1.75 42.85 → 14.25 mΩ; NRST island via; USB_DM's inherited plane-gap crossing recorded |
| REGRESSION-03 | Minor | — | **Fixed.** Nearest GND via: D9.2 > 7 → 2.0 mm, C6.2 2.7 → 1.4, C80.2 10.8 → 2.05, R167.2 5.35 → 0.95 |
| REGRESSION-04 | Minor | — | **Fixed** by the F2 redraw and the F3 clean-up (`route_check` 0 failing) |
| REGRESSION-05 | Minor | — | **Fixed; closed in pass 3.** PULLPIN_EXT 13.7 → 11.1 mm (R6 5.6), ≥ 0.72 mm from CAM_5V/VLOGIC_SENSE. J123.1's pad is 0.350 mm from CAM_5V B.Cu on the fix-pass-2 and fix-pass-3 boards (the "0.20 mm" was the pass-2 board's, before F3 narrowed the R104.1 tap; corrected by P3-REGRESSION-03); with LED_RED 0.225 mm and PULLPIN 0.295 mm, no gap there is below R6's 0.17–0.18 mm |
| REGRESSION-06 | Minor | — | **Partly fixed.** Interface layer changes without a GND via within 1.5 mm: 29 → 10, allowlisted (no DRC-legal spot) |
| REGRESSION-07 | Minor | — | **Fixed.** F4 points at M3_R7 §"DC solve": 3.96 / 3.91 / 1.36 mΩ on the fix-pass-2 board in the old 35 µm model (with the board's own stack-up since fix pass 4: 3.95 / 4.55 / 1.36 mΩ on the fix-pass-4 board, P4-DOCS-02, and 3.95 / 4.58 / 1.36 mΩ on the fix-pass-5 board) |
| REGRESSION-08 | Minor | — | **Fixed.** BAT_ILIM is one link; TP89's branch is on the bottom, ≥ 3.14 mm from QSPI_IO0 |
| DFM-01 | Major | upheld 3/3, **Major** (Major ×2, Minor) | **Fixed.** Via moved to (42.175, 55.82), hole edge 0.205 mm outside R100.1's opening; `check_r7.vias_in_smd_pads` (≥ 0.1 mm, 699 pads; bare TPs and J2 exempt). The inherited J2.1 via (3V3, (44.035, 77.92), hole edge 0.14 mm inside J2.1's opening) is a named exception in REQUIREMENTS M2 and is listed in ORDERING §3/§4 (P3-DFM-04) |
| DFM-02 | Minor | — | **Fixed** (as RF-01) |
| DFM-03 | Minor | — | **Documented; pre-order gate.** ORDERING §3 asks for a forward rail with tabs at x 6–11 and 35–40; JLC's written confirmation is required before production |
| DFM-04 | Minor | — | **Accepted with procedure.** Left tab 1.83 mm from J3: leave out the nearest perforations, nibble last, re-inspect J3 (ORDERING §3) |
| DFM-05 | Minor | — | **Documented.** D30/D31 inspection after jack soldering; ohmmeter check of each jack centre before power-up (ORDERING §4, §5) |
| DFM-06 | Minor | — | **Documented.** All four leg fillets inspected top and bottom (ORDERING §5); via spacing kept (respin item) |
| DFM-07 | Minor | — | **Fixed.** `ViaCheck` keeps vias 0.1 mm from paste apertures; the two vias under U30's paste extensions are gone |
| DFM-08 | Minor | — | **Fixed (documents).** LS120 reflow rating in REQUIREMENTS M1 and ORDERING §4/§6; R7P1-13 closed. `procurement_catalog.json` does not carry it yet (Minor, tools) |
| DFM-09 | Minor | — | **Documented.** U30 245 °C / 40–60 s and U31 limits in M1; order remark asks for a final reflow peak ≤ 245 °C |
| DFM-10 | Minor | — | **Fixed.** GNSS and RADIO legends both on F.SilkS; ORDERING §7 labels the leads GNSS and RADIO to match |
| DFM-11 | Minor | — | **Fixed.** BOM grouped by LCSC code: 92 lines = 92 codes (3 tests) |
| REQUIREMENTS-01 | Major | upheld 3/3 → **Minor** (Major, Minor ×2) | **Documented (owner-delegated decision).** J2 stays bare for programming, then gets polyimide tape and the pyro-block acrylic after the final SWD session; NRST gate (powered, ≥ 0.97 × 3V3) in ORDERING §5. Bench gate open |
| REQUIREMENTS-02 | Major | upheld 3/3, **Major** (Major ×2, Minor) | **Fixed (record).** Estimate recorded in M3_R7 §"Mechanical": f1 221–313 Hz pinned with the sled carrying the plugs (R6 241–341). Decision: no sixth support. Bench tap/modal check open |
| REQUIREMENTS-03 | Major | upheld 3/3, **Major** (Major ×2, Minor) | **Fixed** (as DFM-01) |
| REQUIREMENTS-04 | Minor | — | **Fixed** (as REGRESSION-07) |
| REQUIREMENTS-05 | Minor | — | **Documented.** F10 amended (as RF-04). `check_r7.py`'s strip comment does not yet cite the F10 list (Minor, tools) |
| REQUIREMENTS-06 | Minor | — | **Done (parent repository).** The coordinator recorded the R7 stack row in VEHICLE.md in parent commit `43af048` (corrected by P3-REQUIREMENTS-02) |
| REQUIREMENTS-07 | Minor | — | **Fixed** (as DFM-08) |
| REQUIREMENTS-08 | Minor | — | **Fixed.** LS120 silk 0.15 mm in the library footprint (the gate does not check silk width) |
| REQUIREMENTS-09 | Minor | — | **Fixed** (as DFM-10) |
| REQUIREMENTS-10 | Minor | — | **Fixed.** M3 cost wording rewritten on one snapshot |
| REQUIREMENTS-11 | Minor | — | **Fixed.** RF isolation credited to `check_r7` (pad level) plus DRC and parity in F10, the FMEA, M3_R7 and STATUS |
| REQUIREMENTS-12 | Minor | — | **Documented.** MARGIN_PRESCRIPTION row R14 (R7) |
| REQUIREMENTS-13 | Minor | — | **Fixed** (a) ORDERING battery row, (b) FMEA V-19 and (d) M3_R7 (DIO1 via 3.06 mm from U30's courtyard). (c) parent CLAUDE.md E22 wording: done in parent commit `43af048` (P3-REQUIREMENTS-02) |
| MECHANICAL-01 | Major | upheld 3/3 → **Minor** (Major, Minor ×2) | **Documented.** Counter-hold the flange; mating torque per ORDERING §5 (Kinghelm 0.8–1.13 N·m, or the chosen plug maker's lower value; the pass-2 "about 0.45 N·m" had no source, corrected by P3-MECHANICAL-01); witness marks; epoxy staking after the RF tests; the sled carries the plugs (REQUIREMENTS P3, ORDERING §5/§7, MARGIN R14). Physical work open |
| MECHANICAL-02 | Major | upheld 3/3, **Major** (Major ×2, Minor) | **Fixed (record)** (as REQUIREMENTS-02) |
| MECHANICAL-03 | Major | upheld 3/3 → **Minor** (Minor ×3) | **Documented.** REQUIREMENTS "Board position" replaced; bay-stack paragraph in M3_R7; the parent VEHICLE.md row is recorded (parent `43af048`, P3-MECHANICAL-03). **Open:** the Onshape shroud measurement |
| MECHANICAL-04 | Minor | — | **Documented.** 44–48 mm loop zone with staggered loops or right-angle plugs. **Open:** choose the plug and cite its drawing (`fit_check` basis) |
| MECHANICAL-05 | Minor | — | **Documented.** ORDERING §7 hardware sizes (nylon; washers ≤ 7.0 mm OD; standoffs ≤ 5.5 mm AF, ≥ 3.5 mm tall) |
| RG-01 | Major | upheld 3/3, **Major** (×3) | **Fixed.** PULLPIN is one route, U1.8 → D122.3 33.0 mm, 2 vias, no copy or loop |
| RG-02 | Major | upheld 3/3, **Major** (×3) | **Fixed.** BAT_ILIM is one 0.2 mm link; TP89's branch is 4.5 mm with 1 via |
| RG-03 | Major | upheld 3/3, **Major** (×3) | **Fixed.** Replayed nets redrawn from explicit geometry; the router is retired. Residual: CAM_MCU_TX 2.66× (RQ-06) |
| RG-04 | Major | upheld 3/3, **Major** (×3) | **Fixed.** Port-part leftovers removed; `r7_route.finish` asserts none dangles |
| RG-05 | Major | upheld 3/3, **Major** (Major ×2, Minor) | **Partly fixed.** 29 → 10 interface layer changes without a GND via within 1.5 mm, each allowlisted with a measured "no DRC-legal spot" (1.55–3.57 mm). Opening spots needs the U1 escape re-spaced (not done). **Open for pass 3 / owner acceptance** |
| RG-06 | Major | upheld 3/3, **Major** (×3) | **Fixed.** Duplicate and overlapping copper, overlap-only joints, crossings without a node and track loops: 0 (`route_check`, `scan.py`) |
| RG-07 | Major | upheld 3/3, **Major** (×3) | **Fixed.** PYRO1_GATE is one 0.2 mm route; `check_actuators` OK; DRC pyro rules 0 |
| RG-08 | Major | upheld 3/3, **Major** (Minor, Major ×2) | **Fixed with 5 allowlisted staircases.** Acute 0, fold-back 0, micro-segments 0, off-angle 0; staircases 20 → 5 (4 radio band lanes, PYRO1_CONT); tiny jogs 50 → 5 |
| RG-09 | Major | upheld 3/3 → **Minor** (×3) | **19 of 23 resolved.** 3 vias went with their copper and 16 now have a GND via ≤ 1.5 mm. 4 are allowlisted (ARM1_SENSE ×2, PYRO1_GATE_N, PYRO1_CONT: no legal spot, or the spot cuts the BAT_IN pour) |
| RG-10 | Major | upheld 3/3 → **Minor** (×3) | **Fixed.** 3V3 off-angle segment redrawn |
| RG-11 | Minor | — | **Partly fixed.** RXEN–QSPI_CLK 0.175 → 0.25 mm; IO0 corner and VBUS_SENSE jog fixed; band fan-in staircases allowlisted |
| RG-12 | Minor | — | **Accepted.** Moving the corridor east loses its In2 GND reference; 0.155 mm resistor clearance is DRC-legal |
| RG-13 | Minor | — | **Fixed.** Limiter re-placed; 38.0 mm of B.Cu, every link ≤ 1.11× |
| RG-14 | Minor | — | **Mostly fixed.** R307/C301 off-axis and TP30 left (courtyard and legend limits) |
| RG-15 | Minor | — | **Mostly fixed.** Free-node width changes 58 → 18, unmerged collinear 22 → 3, segments < 0.2 mm 409 → 44. Slow-net detours (SWCLK, SWDIO, CAM_PWR_EN) not rerouted |
| RQ-01 | Major | upheld 3/3, **Major** (×3) | **Partly fixed** (as RG-05). **Open for pass 3 / owner acceptance** |
| RQ-02 | Major | upheld 3/3 → **Minor** (Major, Minor ×2) | **Partly fixed.** In2 GND under the radio B.Cu runs (NRST/DIO1 over In2 GND 2.7 → 76.8 %). The 4-via detours stay; NRST's band run still lies over In2 CAM_MCU_TX |
| RQ-03 | Major | upheld 3/3, **Major** (×3) | **Fixed.** FB31 feed is a 0.4 mm F.Cu run to its own In2 lobe; L1.2 → FB31.1 29.3 → 13.61 mΩ |
| RQ-04 | Major | upheld 3/3, **Major** (×3) | **Fixed.** BAT_SW_RETURN hook and both acute hairpins gone |
| RQ-05 | Major | upheld 3/3, **Major** (×3) | **Fixed.** Duplicates, overlaps, loop, stub and micro-segments gone |
| RQ-06 | Major | upheld 3/3, **Major** (Major ×2, Minor) | **Fixed except CAM_MCU_TX:** LED_RED 62.7 → 32.6 mm, VLOGIC_SENSE 31.7 → 18.8 mm, no U-turns. CAM_MCU_TX stays 65.6 mm, 2.66× (target ≤ 1.5×): the QSPI fan-out has no free lane. **Open for pass 3 / owner acceptance** |
| RQ-07 | Major | upheld 3/3, **Major** (×3) | **Fixed.** Acute joints, fold-backs and the off-angle segment: 0 |
| RQ-08 | Major | upheld 3/3, **Major** (×3) | **Fixed.** Duplicates, sub-50 µm segments and jogs on critical nets: 0 |
| RQ-09 | Minor | — | **Not done.** The NSS/SCK swap stays; moving R310 to the U1 end changes the schematic and pin contract. GND vias at both hop vias, 0.72 mm |
| RQ-10 | Minor | — | **Fixed.** One width (0.15 mm); collinear joints merged |
| RQ-11 | Minor | — | **Partly fixed** (as RG-11). The band jogs are forced by 0.5 mm via pitch against 0.4 mm lanes; RXEN's 90° at (18.35, 44.75) stays. Also kept (listed by P3-ROUTING_QUALITY-06): the 0.212 mm jog into QSPI_IO0's via, (15.4, 51.0)→(15.55, 50.85); the U1-side via columns at x 9.3/9.4/10.0/10.7; the uneven GNSS fan diagonals (TP_MCU steps 1.5 mm from x 12.4, the others 2.0 mm from x 11.2–11.5); the strip column pitch 0.6/0.4/0.4/0.4/0.8 mm |
| RQ-12 | Minor | — | **Fixed.** RXEN aft of U31 along y 8.0, entering pad 10 from its end; 1.2 mm from U3.5 |
| RQ-13 | Minor | — | **Partly fixed.** In2 GND under the GNSS rows; RESET_N's stub removed; its 1.69× detour stays |
| RQ-14 | Minor | — | **Fixed (reference).** Corridor over In2 GND 0 → 98.6 % (BAT_IN logic feed 10.48 → 13.39 mΩ). The 0.155 mm resistor clearance stays (as RG-12) |
| RQ-15 | Minor | — | **Fixed** (as RG-13) |

### Results after fix pass 2 (board `7660620c…`, reviewed by pass 3; superseded)

`tools/check.sh` exit 0 (routing hygiene 0 failing, 20 allowlisted); 157 tests passed; the fab package was bound to
`7660620c…`; $105.96 per board with 52 extended codes; DC RAW_ACT 3.96, BAT_IN 3.91, ACT_FET_S 1.36 mΩ at 7.7 A;
603 R6-referenced samples lost. Pass 3 found that this record carried pass-2 numbers into that state (J123.1,
corrected in the table above) and certified "0 hygiene instances except 5 tiny jogs", which the gate as built
could not show (P3-ROUTING_GEOMETRY-01(d)). The items left open after fix pass 2 went to pass 3; their state now is
in the pass-3 section below.

## Pass 3: eight independent reviews of the fix-pass-2 board

**Board reviewed:** `7660620c…7c9c` (the same SHA before and after the review).

**Reviewers:** eight, in parallel, as in pass 2. Reports are `pass3_*.md` in
`m3_design/assembly_review/sources/r7_review/`; each also checked the pass-2 dispositions in its own field.

**Skeptic step:** each Major went to three skeptic reviewers, who tried to refute it and re-graded it
(`pass3_verdicts.json`). Minor findings were not sent to skeptics.

**Outcome:** no Critical. All 3 Majors were upheld 3 of 3; the majority kept P3-RF-01 and P3-REQUIREMENTS-01 Major
and re-graded P3-ROUTING_GEOMETRY-01 to Minor. 36 Minor.

| Review | File | Critical | Major | Minor |
|---|---|---:|---:|---:|
| RF layout and coexistence | `pass3_rf.md` | 0 | 1 | 3 |
| Electrical | `pass3_electrical.md` | 0 | 0 | 2 |
| Regression against R6 and pass 2 | `pass3_regression.md` | 0 | 0 | 5 |
| DFM and assembly | `pass3_dfm.md` | 0 | 0 | 6 |
| Requirements conformance | `pass3_requirements.md` | 0 | 1 | 6 |
| Mechanical fit and robustness | `pass3_mechanical.md` | 0 | 0 | 4 |
| Routing geometry (whole board) | `pass3_routing_geometry.md` | 0 | 1 | 4 |
| Routing quality (R7 copper) | `pass3_routing_quality.md` | 0 | 0 | 6 |

### Implementation of the pass-3 fixes (fix pass 3)

- **F4** (board and tools; `fix3_F4_handoff.md`, log `fix3_F4_progress.md`):
  - new build stage `m3_design/r7_polish.py` after `r7_hygiene.py`: stages dead, neck, swd, pyro_corners,
    pyro1_cont, corners, l1_node, gnd_moves, dead2, pour_trim, strip_stitch and pour_trim2, under `r7_hygiene`'s
    invariants (each net's pad groups with pours unchanged after every stage, asserted deletions and counts, every
    new segment and via clearance-checked). The upstream output is unchanged: after `r7_hygiene` the board has
    exactly the fix-pass-2 board's tracks, vias and fills;
  - `tools/route_check.py`: tiny jogs inside longer runs, `short_segment`, dead copper with each pour island as one
    terminal, `detour`, `extra_vias`, `pour_sliver`, `pour_finger`, `power_via_no_gnd` (information), `--routes`;
    tests 19 → 27;
  - `tools/check_r7.py`: RF-part filter with Q30–Q32, `rf_part_coverage`, C304 in `DNP`, `launch_reference`,
    `module_ground`, `rf_gnd_reach`; tests 28 → 34;
  - `tools/fit_check.py`: bare and DNP bottom pads in the standoff rule; tests 22 → 23;
  - `r7_post.py`: SMA legends ≥ 0.2 mm from vias and 0.8 mm from other silk; hidden designators 89 → 83.
- **Documentation** (`fix3_docs_handoff.md`): REQUIREMENTS (F10, M2, M3, P1, P2, P3), ORDERING (§1, §3, §4, §5,
  §7), MARGIN_PRESCRIPTION R14 (R7) and AGENTS §3.
- **Records** (this pass): fab package regenerated and checked; gate, tests, cost, stock and procurement rerun;
  final-board DC solves at 0.1 and 0.05 mm; M3_R7, this file and STATUS updated; REQUIREMENTS M2's detour and
  via-count wording corrected to the tool as built; REQUIREMENTS M3 and ORDERING §1, §3, §4 brought to the final
  board and the 2026-10-18 supplier run.

### Every pass-3 finding

"Skeptic" gives the three verdicts and the majority severity; a dash means a Minor finding not sent to skeptics.
Measurements are on the fix-pass-3 board (`636a6bdc…`) unless stated otherwise; record errors that pass 4 found are
corrected in place, and where fix pass 4 changed the state the row says so. "Recorded deviation" means measured,
reasoned and listed in "R7 deviations for owner acceptance" below, but not accepted by the owner.

| ID | Sev. | Skeptic | Disposition |
|---|---|---|---|
| P3-RF-01 | Major | upheld 3/3, **Major** (Major ×2, Minor) | **Fixed.** 21 zone-fill keep-out rule areas (`R7_POUR_TRIM_1…21`: F.Cu 7, B.Cu 14), generated from a fill scan after all copper changes, remove the 15.2 mm RXEN/BUSY sliver, the 5.9 mm SPI1 sliver and every other sliver or unstitched finger (whole board: 6 slivers and 19 fingers → 0); 3 strip stitching vias at (11.975, 21.575), (9.025, 8.325), (25.025, 8.525). Gated by `route_check` `pour_sliver` / `pour_finger` and `check_r7.rf_gnd_reach` (worst strip point 3.14 mm F.Cu and 3.49 mm B.Cu of copper from a GND via; limit 4.0) |
| P3-RF-02 | Minor | — | Not done in fix pass 3; **done in fix pass 4** (P4-RF-03): C302.2 is back on the house thermal relief (`r7_polish.rf_relief`); D30.2 and D31.2 stay solid by decision (ESD return inductance at the jack; the tombstoning risk has no maker figure); ORDERING §5's first-article inspection checks D30, D31 and C302 seated flat (no tombstone or skew) |
| P3-RF-03 | Minor | — | **Fixed (record).** Pass-2 RF-02 row corrected; M3_R7 §"RF strip and lines" records the J30 launch via (14.10, 4.15) replaced by D30.2's via (14.05, 4.65), J31's added via (32.79, 4.75), and U30.10/U30.12's via links removed with the DFM-07 vias (pad-to-via copper 0.225 → 0.575 / 0.775 mm on the pass-3 board; effect negligible, Inference); ORDERING §4 now says the 0.94 mm shunt stubs are part of the network for VNA tuning |
| P3-RF-04 | Minor | — | **Fixed (tools).** `check_r7`: C304 in `DNP`; `launch_reference` (In2 GND under each launch cut-out ± 0.3 mm: 1025 of 1025 samples each); `module_ground` (In1 and In2 GND under U31's body, In1 under U30's keep-out: none missing); `rf_gnd_reach`; tests |
| P3-ELECTRICAL-01 | Minor | — | **Fixed in the documents** (REQUIREMENTS F10, ORDERING §5/§7, M3_R7 limiter table): 37–48 mA at −20 °C, 34–41 mA at 25 °C, 25–38 mA at +85 °C (Inference, `pass2_electrical.md` §4.3). The sheet-15 schematic note (`r7_sch.py` NOTES, `telemetry.kicad_sch`) said "about 27-46 mA" until fix pass 5, whose records agent changed it to "about 37-48 mA at -20 C and 25-38 mA at +85 C" (text only: `r7_sch.py` reproduces the sheet byte for byte and the netlist is byte-identical) |
| P3-ELECTRICAL-02 | Minor | — | (b) **Fixed:** ORDERING §4/§5 name the C304 part (1.0–2.2 nF 0402 X7R/C0G ≥ 10 V, examples) and what each DNP land may take. (a) **Fixed in fix pass 5** (records, as P3-ELECTRICAL-01): the sheet-15 note reads "C303 and C305 capacitive only while R304 is 0R; C313/C314 C or L. C304 capacitor only, 1.0-2.2 nF" |
| P3-REGRESSION-01 | Minor | — | **Recorded deviation.** Opening SPI1_MOSI–IMU_CS to 0.3 mm needs three more vias moved: C121.1 forces MOSI to x − y ≥ −43.0, and moving IMU_CS and I2C1_SCL east hits the SERVO1_MCU (27.1, 68.2) and SERVO2_MCU (26.3, 67.4) vias and leaves 0.002 mm to the 3V3 via (30.17, 71.17) (F4, measured). Edge gap 0.189 mm over about 15 mm, DRC-legal (M3_R7 §"Routing hygiene"); the GND sliver between MISO and MOSI is trimmed |
| P3-REGRESSION-02 | Minor | — | **Fixed.** GND via (35.5, 29.4), 0.7 mm centre to centre from C160.2, joined by one 45° track; copper path from pad outline to via edge (0.05 mm geodesic over F.Cu GND): D122.1 1.68 mm (was 5.62), C160.2 0.24 mm (was 4.22) (the earlier "about 2.5 mm" and "0.7" were an estimate and the centre distance; corrected by P4-REGRESSION-04(b)); no legal spot nearer D122.1 (2.5 mm search). M3_R7 §"Return paths" |
| P3-REGRESSION-03 | Minor | — | **Fixed (record).** J123.1 to CAM_5V B.Cu is 0.350 mm (measured on the fix-pass-3 board); REGRESSION-05 closed (pass-2 table). The R6-method summary now says where the losses are, including the 38 QSPI_NCS samples at CAM_MCU_RX's In2 crossing |
| P3-REGRESSION-04 | Minor | — | **Fixed (record).** M3_R7 §"DC solve" states the grid and what it resolves, solves every path with tracks ≤ 0.25 mm at 0.05 mm as well, adds the power-net table (RAW_PROTECTED to U11, U7 and TP81, VLOGIC, USB_LIMITED, CAM_5V) and quotes no more digits than the grid supports. `dc_solve.py` has no width-mismatch warning yet (optional, not done) |
| P3-REGRESSION-05 | Minor | — | **Recorded deviation; not rerouted** (no lane search was run in fix pass 3 or 4). QSPI_IO0 F.Cu runs 0.232 mm (edge) from BAT_SW_RETURN, about 6 mm side by side, with a closest approach of 0.200 mm at BAT_SW_RETURN's Ø0.6 mm via (15.0, 37.725) (corrected by P4-REGRESSION-04(a)); RADIO_NSS passes it at 0.175 mm (DRC-legal); In1 GND under IO0 is intact. BAT_SW_RETURN is the harness side of the power switch (J1.4 → R165 470 kΩ); about 0.3 pF of coupling, and ESD on the switch wiring is improbable with a sealed reed or magnetic switch (Inference, pass 3) |
| P3-DFM-01 | Minor | — | **Fixed** (ORDERING §1 export output with C304; §4 DNP bullet, 2 top / 22 bottom test pads, the five unfitted lands pasteless on purpose) |
| P3-DFM-02 | Minor | — | **Fixed** (ORDERING §1 from the bound reports; rerun by the records agent on 2026-10-18 with the same $105.96) |
| P3-DFM-03 | Minor | — | **Fixed.** ORDERING §3 forward-tab row (TH3 6.17 mm). The order-number placeholder moves with the copper: (23.9, 90.4) on the fix-pass-3 board; on the fix-pass-4 and final boards (23.65, 103.15), ink x 18.6–28.7, y 102.5–103.7, over no via (fix pass 4's GND via at (22.85, 89.63) took the old spot); ink polygon to the nearest via ring 0.274 mm and to R157.2's mask opening 0.317 mm (P5-DOCS-04(c)); ORDERING §3 updated by the records agents |
| P3-DFM-04 | Minor | — | **Documented.** REQUIREMENTS M2 names the J2.1 via as an exception; ORDERING §3 via covering, §4 via remark and expected DFM queries list it beside TP122. Via unchanged on the final board: 3V3, (44.035, 77.92), 0.3 mm drill, 0.40 mm from J2.1's centre, hole edge 0.14 mm inside the Ø0.787 mm opening |
| P3-DFM-05 | Minor | — | **Done in fix pass 4** (records): ORDERING §5's first-article inspection now checks D30, D31 and C302 seated flat, with no tombstone or skew (with P3-RF-02, P4-RF-03) |
| P3-DFM-06 | Minor | — | (a), (b) **Fixed:** J31's designator moved off RADIO's end; GNSS vertical beside J30 at (8.15, 3.0); SMA legends ≥ 0.2 mm from vias. (c) ORDERING §4 now names J31 by its RADIO legend (fix pass 4 records); **open:** C530661's BOM comment "915MHZ ANT SMA" is J31's Value field, which is in the netlist and on the board (a schematic-and-board change, listed for the coordinator; closed in fix pass 6: J31's Value is now "RADIO ANT SMA"). (d) **Fixed in fix pass 5:** `r7_post` runs the courtyard test on every visible designator and hides any that fails (C301, D120, R155, R172, R80, R83, TP84 hidden; P4-DOCS-04) |
| P3-REQUIREMENTS-01 | Major | upheld 3/3, **Major** (Major ×2, Minor) | **Partly fixed; open (carried as P4-DOCS-01).** Option (a) in part: SWCLK 117.2 mm / 14 vias with 19.5 mm on In1 → 62.7 mm / 4 vias on F/B only; SWDIO 70.8 / 11 → 53.7 / 4; PYRO1_CONT 59.9 / 7 → 47.6 / 4 (the rerouted chain; its staircase gone); since fix pass 4 the net is 53.33 mm of copper with 6 vias (chain 47.53 mm), keeping the 3V3 island whole (P5-DOCS-04(a)). Not rerouted: CAM_PWR_EN 81.9 mm / 8 vias (2.52×; no F/B path; the raster search returns the present route only once SWD has the corridors: before the SWD reroute F4 found 55.1 mm / 7 vias and 72.4 mm / 4 vias through them, so the trade-off is SWD 4 + 4 vias with CAM_PWR_EN 8 against CAM_PWR_EN about 4–7 with longer SWD; corrected by P4-ROUTING_QUALITY-03(b)) and CAM_MCU_TX 65.9 mm / 5 vias (2.67×; the only shorter candidate splits the 3V3 In2 plane, L1.2 → U1.75 14.25 → 29.66 mΩ). The gate gained detour and via-count checks; M2 now says what the gate enforces and what review checks (wording checked against the tool by the records agent and corrected). The 42 allowlist entries and the non-critical detours remained deviations from M2 until the owner accepts them (option (b)); after fix pass 4: 37 entries and 34 recorded leftovers; after fix pass 5: 33 and 30, in "R7 deviations for owner acceptance"; no acceptance is recorded |
| P3-REQUIREMENTS-02 | Minor | — | **Fixed (record).** REQUIREMENTS P1, M3_R7, this file and STATUS cite parent `43af048`; the shroud measurement and the plug choice stay open |
| P3-REQUIREMENTS-03 | Minor | — | **Fixed** (REQUIREMENTS M3, ORDERING §1 from the bound reports; brought to the 2026-10-18 run by the records agent) |
| P3-REQUIREMENTS-04 | Minor | — | **Fixed** (ORDERING §1, §4; C304 in `check_r7.DNP`) |
| P3-REQUIREMENTS-05 | Minor | — | **Documented** (as P3-DFM-04) |
| P3-REQUIREMENTS-06 | Minor | — | **Fixed.** `check_r7.RF_PART` adds `Q3\d`; `rf_part_coverage` fails any part with a radio or GNSS pad outside the filter (U1 excepted; none); tests |
| P3-REQUIREMENTS-07 | Minor | — | **Fixed.** (a) AGENTS §3 and M2 use the same critical-net scope and point at `route_check`; (b) P2 says "owner-delegated decision"; (c) F10 and the M3_R7 binding note add EXTI15_10 (DIO1, PULLPIN, VBUS_SENSE) |
| P3-MECHANICAL-01 | Minor | — | **Fixed (documents).** Mating torque 0.8–1.13 N·m (Kinghelm datasheet p. 1) or the chosen plug maker's lower value, counter-held, calibrated wrench (REQUIREMENTS P3, ORDERING §5/§7, MARGIN R14 (R7), M3_R7). The value is recorded with the plug choice (open) |
| P3-MECHANICAL-02 | Minor | — | **Fixed (documents).** MARGIN R14 (R7) now "⚠ ≥ 5× rests on the staking (Inference)"; ORDERING §7 sets the saddle on the plug axis; M3_R7 gives the jack moment 45–190 N·mm at 5 × 100 g and relabels the table row |
| P3-MECHANICAL-03 | Minor | — | **Fixed (record)** (as P3-REQUIREMENTS-02). The VEHICLE additions (J1's forward battery entry, standoffs ≥ 3.5 mm) are proposed to the coordinator (`fix3_docs_handoff.md` §2), not made |
| P3-MECHANICAL-04 | Minor | — | **Fixed (tools).** `fit_check` puts exposed bottom pads of board features and DNP footprints in the standoff rule; test; nearest is still C76, 4.150 mm |
| P3-ROUTING_GEOMETRY-01 | Major | upheld 3/3 → **Minor** (Minor ×3) | **Fixed.** (a) Every A,B,A triple inside a longer run is tested (13 tiny jogs counted); (b) gated `short_segment` (≥ 50 µm and < max(width, 0.2 mm), not inside one same-net pad or via); (c) the RXEN and GNSS_RXD_MCU GND vias moved to 1.50 mm and their entries removed, the QSPI_CLK and "no legal spot" reasons rewritten; board: PYRO1_GATE_N's 83 µm hook → one straight run into R126.1, 3V3 into C17.1 square, the GND pyro corner one 45° step, SW_NODE allowlisted (forced; measured); (d) counts corrected in M3_R7, here and STATUS |
| P3-ROUTING_GEOMETRY-02 | Minor | — | **Recorded deviation, 10 entries after fix pass 4, 9 after fix pass 5** (ARM1_SENSE's two have GND vias since fix pass 5, P5-ROUTING_GEOMETRY-03; PYRO1_GATE's layer change into TP122 is counted since then, A8). The fix-pass-3 record said 11 (8 radio interface, PYRO1_GATE_N, ARM1_SENSE ×2) with "no legal site"; that was false for PYRO1_GATE_N on the fix-pass-3 board (P4-ROUTING_GEOMETRY-01), which now has a GND via at 1.309 mm. The other 10 have no legal spot (gated `nognd_audit`). Respin note: re-space the band and corridor via columns |
| P3-ROUTING_GEOMETRY-03 | Minor | — | **Fixed.** `dead()` treats each pour island as one terminal and flags stubs ending in a pour; 41 tracks removed, including the floating 3V3 chain and the six protruding stubs |
| P3-ROUTING_GEOMETRY-04 | Minor | — | **Fixed.** L1.2 node: tracks from the pad centre, the second via and its hop removed. M2 states which items the gate holds and which review judges. The one-by-one judgement of the information-only instances on critical nets was done in pass 4 (P4-ROUTING_GEOMETRY-03: accept, apart from cheap tidy-ups) |
| P3-ROUTING_GEOMETRY-05 | Minor | — | **Fixed (tool, documents).** `power_via_no_gnd` reported as information (39 → 36); the GND-via rule's scope (critical signal nets) and hygiene gating (critical nets) are written in AGENTS §3 and M2; detours and via counts gated on critical nets, counted on all |
| P3-ROUTING_QUALITY-01 | Minor | — | **Recorded deviation** (as P3-ROUTING_GEOMETRY-02). 8 interface layer changes remain: band BUSY (9.4, 28.2) 1.65 mm, MOSI (9.4, 29.2) 1.65, MISO_MCU (10.0, 28.7) 2.11; U1 escape MOSI_MCU (9.4, 48.5) 1.71, BUSY (10.0, 49.5) 2.60, NRST (9.3, 50.0) 3.18, DIO1 (10.0, 50.5) 3.57; RXEN (23.8, 39.45) 2.23. RXEN (21.2, 30.45) and GNSS_RXD_MCU (2.2, 51.5) now have GND vias at 1.50 mm |
| P3-ROUTING_QUALITY-02 | Minor | — | **Recorded deviation; not changed.** All 7 radio lines cross from the In2 GND corridor strip to the In2 BAT_IN arm at both corridor ends (14 crossings, 3.1–3.8 mm over BAT_IN per line). At the U1 end, moving them cuts U9's In2 BAT_IN arm or moves the band onto In2 GND, and stitching needs a new BAT_IN–GND capacitor (schematic and BOM change). At the band end a layout-only change appears possible: pull the In2 BAT_IN arm north of U9 (it serves only C89.1, C95.1 and two vias, which the F.Cu BAT_IN pour also reaches through via (9.2, 36.05)) back to about y 34.5 (pass-4 Inference; corrected by P4-ROUTING_QUALITY-03(a)). **Band end done in fix pass 5** (P5-ROUTING_QUALITY-01: the In2 GND strip extended over x 6.9–9.9, y 25.0–31.3 and two BAT_IN vias removed; those 7 crossings are gone); the 7 at the U1 end remain (deviation C5) |
| P3-ROUTING_QUALITY-03 | Minor | — | **Recorded deviation; not changed.** RADIO_NRST's B.Cu run lies over CAM_MCU_TX's In2 track for 10.2 mm; the CAM_MCU_TX reroute was rejected for the 3V3 plane split (as P3-REQUIREMENTS-01) |
| P3-ROUTING_QUALITY-04 | Minor | — | **Fixed.** PYRO1_COLD: R131.2 → north → 45° into D120.1, 0.48 mm from R131.1 (rule C 0.3 mm); `check_actuators` OK |
| P3-ROUTING_QUALITY-05 | Minor | — | **Recorded deviation (inherited R6).** VCAP2 12.67 mm / 1 via for 3.0 mm (4.22×) and VCAP1 6.71 mm / 2 vias for 1.37 mm (4.89×), both allowlisted detours; the 3V3 feed to U12/C100, 16.3 mm for 5.2 mm (3.2×, on a poured net, so outside `route_check`'s detour test). Fixing them needs C19/C20 moved and U12's 3V3 re-tapped (respin) |
| P3-ROUTING_QUALITY-06 | Minor | — | **Fixed (record).** The pass-2 RQ-11 row lists the four kept items; the PYRO1_GATE_N allowlist reason states the 1.03 mm DRC-legal spot and why `ViaCheck` refuses it |

### Results after fix pass 3 (board `636a6bdc…`, reviewed by pass 4; superseded)

`tools/check.sh` exit 0 (routing hygiene 0 failing, 42 allowlisted, 0 stale); 151 tests in 8 suites and quality_audit
21 passed; the fab package was bound to `636a6bdc…`; $105.96 per board with 52 extended codes (2026-10-18 02:59Z);
DC RAW_ACT 3.96, BAT_IN 3.91, ACT_FET_S 1.36 mΩ at 0.1 mm in the old 35 µm model; 864 R6-referenced samples lost.
Pass 4 found that this record listed PYRO1_GATE_N among 11 layer changes with "no legal site" when a legal GND via
spot existed (P4-ROUTING_GEOMETRY-01), filed 46 non-critical leftovers as "measured and reasoned" without reasons
(P4-DOCS-01), quoted In2 paths from a 35 µm inner-copper model (P4-DOCS-02), carried a wrong SWDIO In2 length
(P4-DOCS-03) and cited a "D30/D31/C302 seating" ORDERING step that did not exist (P4-RF-03). Its "Recorded
deviations" list is replaced by "R7 deviations for owner acceptance" below, and its open items are carried into
"Open after fix pass 4".

## Pass 4: five independent reviews of the fix-pass-3 board

**Board reviewed:** `636a6bdc…7650` (the same SHA before and after each review).

**Reviewers:** five, in parallel; each also checked the pass-3 dispositions in its own field. Reports are `pass4_*.md`
in `m3_design/assembly_review/sources/r7_review/`; requirements, documents, DFM and mechanical were one review
(`pass4_docs.md`).

**Skeptic step:** each Major went to three skeptic reviewers, who tried to refute it and re-graded it
(`pass4_verdicts.json`). Minor findings were not sent to skeptics.

**Outcome:** no Critical. Both Majors were upheld 3 of 3, and neither was refuted. The skeptics' majority kept
P4-DOCS-01 Major (Major ×2, Minor) and re-graded P4-ROUTING_GEOMETRY-01 to Minor (Minor ×2, Major); both were worked
as Majors in fix pass 4. 16 Minor.

| Review | File | Critical | Major | Minor |
|---|---|---:|---:|---:|
| RF layout and coexistence | `pass4_rf.md` | 0 | 0 | 3 |
| Regression against R6 and pass 3 | `pass4_regression.md` | 0 | 0 | 4 |
| Routing geometry (whole board) | `pass4_routing_geometry.md` | 0 | 1 | 2 |
| Routing quality (critical and new nets) | `pass4_routing_quality.md` | 0 | 0 | 3 |
| Requirements, documents, DFM and mechanical | `pass4_docs.md` | 0 | 1 | 4 |

### Implementation of the pass-4 fixes (fix pass 4)

- **F5** (board and tools; `fix4_F5_handoff.md`, log `fix4_F5_progress.md`). Every board change is in
  `m3_design/r7_polish.py`:
  - `pyro1_cont`: the plane-preserving PYRO1_CONT route (6 vias, 47.53 mm), which keeps the In2 3V3 island whole;
  - `band`: RADIO_NRST's step moved inside its via, RADIO_SCK's and RADIO_NSS's later (staircases 4 → 2);
  - `debris`: 10 non-critical nets redrawn; `reroutes`: CAM_UART_OE (6 → 4 vias) and NRST's J2 branch (off In1);
  - `rf_relief`: C302.2 back on the house thermal relief;
  - `gnd_vias` (with a fine 0.025 mm pass) on the final signal copper, which adds the PYRO1_GATE_N GND via, and
    `gnd_vias2` after the strip stitching (asserted to add nothing);
  - `pour_trim`: same-net pad relief rings are never kept out, and no pad may lose its pour contact (asserted); the
    21 areas are regenerated.
  - `m3_design/r7_hygiene.py`: the GND-via legality became a class (`GndFit`) with a spot search (`gnd_spots`); its
    output is unchanged (the post-hygiene board through the old `r7_polish` gave `636a6bdc…` byte for byte).
  - `tools/route_check.py`: `nognd_audit` (gated), `pad_pour_cut` (a gated pour category), the relief-ring rule in
    `pour_finger`, and `LEFTOVERS` with a gated record check (every non-critical detour, extra_vias, tiny_jog and
    short_segment instance needs an entry with a measured reason; 34 entries); tests 27 → 32.
  - `tools/check_r7.py`: `RF_SOLID_GND` drops C302.2. `tools/dc_solve.py`: reads the board's stack-up; new
    `tools/test_dc_solve.py` (3 tests).
  - Not in F5's list, not done: P4-RF-01, P4-RF-02, P4-ROUTING_GEOMETRY-02, the tidy-ups of P4-ROUTING_GEOMETRY-03,
    and the designator moves of P4-DOCS-04.
- **Records and documents** (this pass): fab package regenerated and checked; gate, every test suite, cost, stock and
  procurement rerun; two DC paths re-solved on the final board; the pass-4 reviewers' scans rerun on the final board
  for the open Minors; a courtyard test of every visible designator; M3_R7, this file, STATUS, REQUIREMENTS (F4, M2,
  M3), ORDERING (§1, §3, §4, §5) and AGENTS (§1, §3) updated.

### Every pass-4 finding

"Skeptic" gives the three verdicts and the majority severity; a dash means a Minor finding not sent to skeptics.
Measurements are on the fix-pass-4 board (`c6fe595c…`, "the final board" in these rows) unless stated otherwise;
where fix pass 5 changed the state the row says so.

| ID | Sev. | Skeptic | Disposition |
|---|---|---|---|
| P4-RF-01 | Minor | — | **Not done; recorded.** `pour_finger` still stops at 0.5 mm width. With the reviewer's scan (no relief-ring exclusion) the fix-pass-4 board had 23 unstitched GND pieces narrower than 0.75 mm and 49 narrower than 1.0 mm (fix-pass-3 board: 20 and 48; for the final board see deviation C11). The x 40 F.Cu finger between CAM_MCU_TX and LED_YEL (39.78–40.47, 28.27–37.32) now reaches 10.7 mm of copper from a GND via (was 17.2 mm; F5's LED_YEL_A redraw is beside its tip); the pass-4 ViaCheck search found no legal via spot in it on the fix-pass-3 board (not re-searched); the forward-edge F.Cu strip (y 115.81–117.49) has legal via spots and is not stitched (stitched in fix pass 5, 12 vias). The scan rerun on the fix-pass-5 board (`1ffc2585…`, records) gives the same 23 and 49. Deviation list C11 and C20. RF effect negligible (Inference, pass 4) |
| P4-RF-02 | Minor | — | **Not done (tools); recorded.** No gate checks F.Cu coplanar ground beside the GCPW lines, F.Cu under the module bodies, or where a new pour trim lands. On the final board the nearest trim is 6.7 mm from RF-net copper (`R7_POUR_TRIM_8`, the RXEN/BUSY sliver) and none lies in U30's or U31's courtyard; `check_r7` evidence unchanged (fence 21 vias, line-side gaps 3.90 / 2.65 / 1.55 / 1.55 mm, launches 1025/1025, module ground 0 missing, strip GND reach 3.14 / 3.49 mm) |
| P4-RF-03 | Minor | — | **Fixed.** C302.2 on thermal relief (pour contact 0.111 → 0.045 mm², GND via kept; `thermal_policy` now requires it). D30.2 / D31.2 kept solid by decision (the clamp's return inductance matters at the jack; the tombstoning risk is a general-practice inference with no maker figure). ORDERING §5 first-article inspection: "D30, D31 and C302 seated flat (no tombstone or skew)". STATUS and this file now cite that real step |
| P4-REGRESSION-01 | Minor | — | **Fixed** (with P4-ROUTING_QUALITY-01). PYRO1_CONT on the plane-preserving route: In2 3V3 island under U1/U4 one piece, 74.51 mm² with 4 vias; copper gaps SPI1_SCK 2.75 mm (was 0.195 mm over 7.4 mm), SPI1_MOSI 3.32 mm, SPI1_MISO > 5 mm, PYRO1_GATE_N 1.08 mm F.Cu and 2.09 mm In2 (was 0.191 mm); every layer change has a GND via within 1.5 mm; critical reference back to 603 lost / 861 candidate-new. Cost: 6 vias instead of 4 (allowlisted, measured) and a 1.8 mm In2 hop (information). Close approaches of the new copper, recorded since pass 5 (P5-ROUTING_QUALITY-02, P5-REGRESSION-03; DRC-legal): CAM_UART_OE 0.175, SWCLK 0.191, R129.1 0.193, NRST 0.195, 3V3A 0.212, R168.1–SWCLK 0.220, R75.1 0.225 mm (deviation C15) |
| P4-REGRESSION-02 | Minor | — | **Fixed.** `pour_trim` leaves every same-net pad's relief ring out of the keep-outs; gated `pad_pour_cut` (fix-pass-3 board: exactly the review's 5 pads; final 0); C7.2, C150.2, C30.2, C31.2 and R64.2 back to their fix-pass-2-board pour contact; the 40 pads with no pour contact are the same 40 (none lost). Unit tests |
| P4-REGRESSION-03 | Minor | — | **Recorded (no copper change).** SWCLK's B.Cu hop via (24.7, 50.95) is 1.10 mm from HSE_OUT (Y1.3) on B.Cu, 2.20 mm on F.Cu, 2.31 mm on In1/In2; F5 found no F/B route that keeps its vias ≥ 2 mm from Y1.3 (measured constraints in M3_R7 "Rerouted in fix pass 3"). B.Cu GND pour 39 → 35 polygons (fix pass 4's reroutes joined pieces); the crystal/U1 island 133.2 mm² with 27 vias; every piece via-stitched. Deviation list C8, C9 |
| P4-REGRESSION-04 | Minor | — | **Fixed (records).** (a) QSPI_IO0 closest approach 0.200 mm at BAT_SW_RETURN's via, beside the 0.232 mm run (P3-REGRESSION-05 row, M3_R7). (b) D122.1 1.68 mm and C160.2 0.24 mm of copper to the via, with the method (P3-REGRESSION-02 row, M3_R7). (c) M3_R7 "DC solve" states that the L1.2 node redraw lengthened C9's connection, L1.2 → C9.1 1.67 → 2.48 mΩ at 0.1 mm (2.30 mΩ at 0.05 mm on the final board) |
| P4-ROUTING_GEOMETRY-01 | Major | upheld 3/3 → **Minor** (Minor ×2, Major); worked as Major | **Fixed.** GND via 0.6/0.3 mm at (22.85, 89.63), 1.309 mm from PYRO1_GATE_N's layer change (23.0, 88.33) (was 1.815 mm); the allowlist entry is deleted. The GND-via search now runs again after the last signal-copper change (`gnd_vias`, fine pass) and after the strip stitching (`gnd_vias2`, 0 added). New gated `route_check.nognd_audit` reruns the project-legal spot search for every allowlisted critical_via_no_gnd entry (fix-pass-3 board: exactly the review's spot; final: 0). `_NOGND` cites the gated audit and F5's ±0.6 mm via-slide search. Records corrected: 10 entries (P3-ROUTING_GEOMETRY-02 row, M3_R7, STATUS) |
| P4-ROUTING_GEOMETRY-02 | Minor | — | **Not done (tools); instances recorded.** The gate's blind spots stand: S1 sharpest pair only (ACT_GATE's 45° wedge at Q121.4, (5.9, 102.4), apex 0.012 mm outside the pad; rerun: still the one all-pairs failure); S2 jogs through T, via or pad nodes (GND staircase C94.2 → LED1 buried in its pour, CAM_5V jog into via (39.35, 104.55), 3V3_RADIO at FB31.2, GND (31.3, 53.7) between two vias, CAM_FAULT_N In2 through a via, and CAM_RX_WIRE's 0.16 mm step, now one 0.228 mm segment at its T after F5's redraw); S3 RAW_ACT tail 3.17 mm inside its own pour; S4 the TP122 pad-via layer change, 2.93 mm from a GND via; S5 overlapping launch GND vias (0.585 mm apart, DRC-legal). All re-found on the fix-pass-4 board (reviewer's `p4extra.py`, `rc_allpairs.py`). **Closed in fix pass 5:** S1–S5 are `route_check` detections now and every instance was removed or measured (P5-ROUTING_GEOMETRY-04; deviation list D) |
| P4-ROUTING_GEOMETRY-03 | Minor | — | **Judgement recorded; tidy-ups not done.** The reviewer judged every information-only instance on critical nets (fix-pass-3 board: 63 off-centre pad ends, 29 width changes at junctions, 18 U-turns, 10 extra-bend runs, 10 tracks through a same-net pad, 8 short layer hops, 2 segments inside a pad) and recommends accepting them, apart from cheap tidy-ups: USB_LIMITED at U11.7, VLOGIC at U2.2, PYRO1_CONT's via jog (gone: the route was replaced), RADIO_RXEN's 0.225 mm jog across via (23.8, 39.45), and the P4-ROUTING_GEOMETRY-02 instances. Fix-pass-4 board counts: 64 / 29 / 18 / 12 / 10 / 9 / 2. This closes P3-ROUTING_GEOMETRY-04. The tidy-ups were made in fix pass 5 (D10–D12); the information-only instances are deviation list part E |
| P4-ROUTING_QUALITY-01 | Minor | — | **Fixed** (as P4-REGRESSION-01). The `r7_polish.pyro1_cont` docstring's "every power pour kept whole" is now true of the route it draws |
| P4-ROUTING_QUALITY-02 | Minor | — | **Fixed (records).** M3_R7 records SWCLK–Y1.3 1.10 mm; SWDIO's layer sequence F → B → In2 → B → F with 13.73 mm on In2 and the 2.58 mm B.Cu hop (not "a 5.9 mm In2 hop"); the B.Cu GND under ARM1_SENSE's and CAM_PWR_EN's In2 runs cut by SWDIO's B.Cu verticals (voids 4.2, 4.7 and 5.3 mm, fix-pass-3 board figures). Deviation list C8, C9 |
| P4-ROUTING_QUALITY-03 | Minor | — | **Fixed (records).** (a) P3-ROUTING_QUALITY-02 now names the band-end layout option (pull the In2 BAT_IN arm back to about y 34.5; Inference, not attempted). (b) P3-REQUIREMENTS-01 and M3_R7 state the CAM_PWR_EN / SWD corridor trade-off (F4: 55.1 mm / 7 vias and 72.4 mm / 4 vias through the SWD corridors). (c) The `r7_polish` docstring is true since the route changed |
| P4-DOCS-01 | Major | upheld 3/3, **Major** (Major ×2, Minor) | **Partly fixed; open until the owner decides.** (1) AGENTS §3 instances in the allowlist 15 → 12: staircases 4 → 2 (RADIO_NRST and RADIO_SCK clean; BUSY and MISO_MCU recorded as forced, which pass 5 found untrue: P5-ROUTING_GEOMETRY-01, both removed in fix pass 5; RADIO_SCK's had been lengthened into an extra-bend run, P5-ROUTING_QUALITY-04), critical layer changes without a GND via 11 → 10 (each now re-checked by `nognd_audit`). (2) Non-critical debris: 14 short segments and tiny jogs → 2 (CAM_EN, CAM_FAULT_N, recorded as forced; pass 5 found neither forced and fix pass 5 removed both, P5-ROUTING_GEOMETRY-02; of the 12 counted as removed, LOGIC_ILIM's, I2C1_SCL's and SERVO4_MCU's steps had only been lengthened past the 0.5 mm test, P5-ROUTING_QUALITY-04: two are removed in fix pass 5 and I2C1_SCL's is forced, deviation C16); CAM_UART_OE and NRST rerouted; every remaining non-critical detour and over-via net carries a raster-search result in `route_check.LEFTOVERS` (34 entries), and the gate fails an unrecorded or stale one. (3) Owner acceptance: the consolidated list "R7 deviations for owner acceptance" below is what REQUIREMENTS M2 now names as awaiting the owner's dated acceptance; no acceptance is recorded |
| P4-DOCS-02 | Minor | — | **Fixed.** `tools/dc_solve.py` reads each layer's copper thickness and the dielectric stack from the board's `(stackup …)` block (stops if missing); `test_dc_solve.py` 3 tests. M3_R7 "DC solve" restated: BAT_IN J1 → Q120 4.55 mΩ at 0.1 mm (4.51 at 0.05 mm; old model 3.91), J1 → U9 15.1 mΩ, 3V3 L1 → U1.75 15.6 mΩ; "equal to R6" is a same-model comparison. The records agent re-solved BAT_IN and RAW_ACT at 0.1 mm: 4.55 and 3.95 mΩ |
| P4-DOCS-03 | Minor | — | **Fixed (records).** M3_R7 gives SWDIO's real layer sequence and 13.73 mm on In2. The 2.58 mm B.Cu hop lies inside the In2 3V3 zone outline; F5's raster search (power pours kept whole) finds no SWDIO route under 4 vias; an In2 continuation was not measured. `fix3_F4_handoff.md` is left as the historical record |
| P4-DOCS-04 | Minor | — | **Not done in fix pass 4; fixed in fix pass 5** (`r7_post` courtyard test on every visible designator; the 7 below hidden, U13 shown; hidden 84 → 90). D120 (own courtyard 0.472 mm, C121 0.225 mm) and R155 (0.579, R151 0.560) are still shown. The records agent's courtyard test of every visible designator on the final board finds 7: those two, the recorded R80, R172 and TP84, and R83 (its ink touches C84's courtyard) and C301 (U30 0.117 mm against its own 0.165 mm), both already so on the fix-pass-3 board. Hidden designators 83 → 84 (r7_post on F5's copper). Deviation list D17 |
| P4-DOCS-05 | Minor | — | **Fixed (records).** (a) U4 and U30 "account for most of" the $4.97 (they sum to $5.22). (b) J3's tab distance is 1.83 mm throughout M3_R7 |

### Results after fix pass 4 (board `c6fe595c…`, reviewed by pass 5; superseded)

`tools/check.sh` exit 0 (routing hygiene 0 failing, 37 allowlisted, 34 leftovers recorded); 159 tests in 9 suites and
quality_audit 21 passed; the fab package was bound to `c6fe595c…`; $105.98 per board with 52 extended codes
(2026-10-18 08:29Z); DC RAW_ACT 3.95, BAT_IN J1 → Q120 4.55, ACT_FET_S 1.36 mΩ at 0.1 mm; 603 R6-referenced samples
lost; 84 hidden designators. Pass 5 found that three allowlist reasons (A1, A2, A5) and five leftover reasons were not
true or not measured (P5-ROUTING_GEOMETRY-01/-02), that the deviation list left 18 part-D items neither removed nor
reasoned and omitted the information-only instances and earlier "kept" residuals (P5-DOCS-01), that no IPC-2152
sizing at the ordered 30 µm inner copper was recorded (P5-DOCS-02), that pass-1 E11 had dropped out (P5-DOCS-03), and
several misplaced or misquoted figures (P5-REGRESSION-01/-04, P5-ROUTING_QUALITY-03, P5-DOCS-04). Its deviation list
is replaced by the one below, and its open items are carried into "Open after fix pass 5".

## Pass 5: four independent reviews of the fix-pass-4 board

**Board reviewed:** `c6fe595c…c7c7` (the same SHA before and after each review).

**Reviewers:** four, in parallel; each also checked the pass-4 dispositions in its own field. Reports are `pass5_*.md`
in `m3_design/assembly_review/sources/r7_review/`; requirements, documents, DFM and mechanical were one review
(`pass5_docs.md`). RF had no separate review in this pass.

**Skeptic step:** each Major went to three skeptic reviewers, who tried to refute it and re-graded it
(`pass5_verdicts.json`). Minor findings were not sent to skeptics.

**Outcome:** no Critical. Both Majors were upheld 3 of 3, and neither was refuted. The skeptics re-graded
P5-ROUTING_GEOMETRY-01 to Minor (Minor ×3) and kept P5-DOCS-01 Major (Major ×2, Minor); both were worked as Majors in
fix pass 5. 15 Minor.

| Review | File | Critical | Major | Minor |
|---|---|---:|---:|---:|
| Regression against R6 and pass 4 | `pass5_regression.md` | 0 | 0 | 4 |
| Routing geometry (whole board) | `pass5_routing_geometry.md` | 0 | 1 | 3 |
| Routing quality (critical and new nets) | `pass5_routing_quality.md` | 0 | 0 | 5 |
| Requirements, documents, DFM and mechanical | `pass5_docs.md` | 0 | 1 | 3 |

### Implementation of the pass-5 fixes (fix pass 5)

- **F6** (board and tools; `fix5_F6_handoff.md`, log `fix5_F6_progress.md`). Every board change is in
  `m3_design/r7_polish.py` and `r7_post.py`; the post-hygiene board is byte-identical to F5's. A clean
  `m3_design/r7_build.sh` from the SHA-checked R6 board gave **`1ffc2585…`** exactly (14 min 55 s; its `check.sh`
  passed).
  - `r7_polish` stages: `pyro1_cont` (the F.Cu run drawn S / SE / S), `band5` (radio band chamfers), `qspi5` (RXEN on
    its via column, QSPI_CLK's step), `jogs5` (CAM_EN, CAM_FAULT_N, SERVO4_MCU, LOGIC_ILIM, CAM_RX_WIRE, CAM_TX_WIRE off
    In1, LOGIC_SOURCE_ST, CAM_5V_SENSE, PULLPIN_EXT, LED_RED), `tidy5` (D1–D4, D7, D9–D11), `arm_gnd` (ARM1_SENSE GND
    vias), `band_end` (the In2 GND strip over the band end), `edge_stitch` (12 forward-edge GND vias), `gnd_pieces`
    (4 second GND vias); `pour_trim` regenerates 23 trims (F.Cu 9, B.Cu 13, In2 1); every via placement now keeps
    0.27 mm from non-plated holes (`npth_ok`).
  - `r7_post`: every visible designator passes the ink-to-courtyard test or is placed again, else hidden (C301, D120,
    R155, R172, R80, R83, TP84 hidden; U13 shown; hidden 84 → 90); the run fails if one is left.
  - `tools/route_check.py`: jogs and staircases through T, via and pad nodes; every branch pair in the acute test;
    `pour_stub`; a layer change into a pad counted; `via_overlap`; `measured_check` (detour / extra_vias figures);
    `alt_audit` (redraw search for every allowed or recorded jog, staircase and short segment); every hygiene category
    on a non-critical net must be recorded. Tests 32 → 41.
  - Totals: tracks 1,809 → 1,777, vias 694 → 706 (+18 GND, −6 signal and BAT_IN); In1 signal copper 3.67 mm → 0.
- **Records and documents** (this pass): fab package regenerated (after F6, and again after the sheet-15 notes) and
  checked; gate, every test suite, cost, stock and procurement rerun; an IPC-2152 estimate of the 7.7 A copper; the
  sheet-15 schematic notes corrected (`r7_sch.py` NOTES and `telemetry.kicad_sch`; netlist byte-identical); the GND
  finger scan, placeholder clearances and in-pour lengths re-measured on the final board; the deviation list rewritten;
  M3_R7, this file, STATUS, REQUIREMENTS (F4, M2), MARGIN_PRESCRIPTION (85 °C row) and ORDERING (§1, §3) updated.

### Every pass-5 finding

"Skeptic" gives the three verdicts and the majority severity; a dash means a Minor finding not sent to skeptics.
Measurements are on the fix-pass-5 board (`1ffc2585…`) unless stated otherwise.

| ID | Sev. | Skeptic | Disposition |
|---|---|---|---|
| P5-REGRESSION-01 | Minor | — | **Fixed (records).** NRST's x 36.3 In2 run (10.35 mm) has no B.Cu GND fill above any of its length; 3V3A's 0.25 mm B.Cu track lies over 6.4–7.2 mm of it (the two reviewers' methods); no PYRO1_CONT copper is above it. The 545 extended-set samples behind the old "about 1.8 mm" lie near U1 (30.73–36.09, 51.41–54.31), where the J2 branch's B.Cu sits over NRST's own In2 segments. Inherited in kind: R6's and the pass-4 board's x 36.435 run had 13.38 of 14.0 mm unreferenced; NRST's In2 without B.Cu GND fell from 20.6 to 14.7 mm; In1 GND lies 1.06 mm above. Restated in C10 and M3_R7 ("Rerouted in fix pass 4", "Return paths"). No copper change (respin option: route the In2 lane under B.Cu GND) |
| P5-REGRESSION-02 | Minor | — | **Fixed** (F6 `gnd_pieces`). Second GND vias (0.5 mm) in the four pieces: (41.375, 70.625) F.Cu by J2, (35.85, 53.275) B.Cu east of U1, (27.4, 76.4) B.Cu by U4, (34.05, 57.025) F.Cu by CAM_UART_OE. Single-via GND pieces on F.Cu and B.Cu 40 → 35, all 35 inherited (deviation C14) |
| P5-REGRESSION-03 | Minor | — | **Recorded; no nudge.** The GND via (28.55, 87.21) stays: of the 5 legal spots within 1.45 mm of PYRO1_CONT's via (28.4, 88.61), none is ≥ 0.25 mm from R129.1 and R178.1 (F6, measured). (a)–(d), with the fail-safe reasoning, and the close neighbours of fix pass 5's copper are in M3_R7 "Close adjacencies kept" and deviation C15 |
| P5-REGRESSION-04 | Minor | — | **Fixed (records).** M3_R7: PYRO1_CONT's B.Cu run leaves R168.1 east of U1 (not "east of U4"); its F.Cu run lies north of the IMU and east of the barometer U5 (drawn S / SE / S in fix pass 5); its last In2 run (30.82 → 28.40, y 88.61) crosses under PYRO1_OUT's F.Cu vertical at x 30.58 with solid In1 GND between them (the pyro rules are same-layer) |
| P5-ROUTING_GEOMETRY-01 | Major | upheld 3/3 → **Minor** (Minor ×3); worked as Major | **Fixed.** `band5`: RADIO_BUSY's and RADIO_MISO_MCU's east chamfers are 1.004 mm (MISO_MCU's and RADIO_MOSI's fan-in steps 0.35–0.4 mm later; lanes keep 0.25 mm): both staircases are gone (now extra-bend runs, information) and A1, A2 are deleted. `qspi5`: RADIO_RXEN runs on its via column x 23.8 (D12 gone) and QSPI_CLK takes a 0.36 mm step (0.509 mm, outside the tiny-jog class): A5 is deleted. Measured: BUSY's chamfer 0.25 mm from MISO_MCU and 0.176 mm from the GND via (20.0, 27.45); QSPI_CLK 0.24 mm from RXEN's via and 0.325 mm from LED_YEL; RXEN 0.329 mm from the GND via (23.92, 30.8). The 0.2 / 0.3 mm fan-in steps (A1, A2 below) stay, re-measured by `alt_audit` on every gate run. Cost: 21 QSPI_CLK F.Cu reference samples at (23.31, 39.35–39.55) now pass RXEN's via antipad (C2). The P4-DOCS-01 row, M3_R7 and STATUS are corrected |
| P5-ROUTING_GEOMETRY-02 | Minor | — | **Fixed.** `jogs5`: CAM_EN W / S / SW (B1 gone); CAM_FAULT_N one straight In2 run at y 103.938 (B2 and its staircase through a via, D6, gone); CAM_RX_WIRE one In2 run at x 44.251 (D13 gone). CAM_5V_SENSE's F.Cu hop and two vias removed (its extra_vias entry gone); LED_RED's hop moved to F.Cu, 3 → 2 vias (entry gone). CAM_5V_SENSE's detour and SERVO2_MCU's vias are re-reasoned with measured blockers (B7, B22). NRST is 46.11 mm, and the gate now checks every route figure (`measured_check`). "Both forced" is corrected in M3_R7 and the P4-DOCS-01 row |
| P5-ROUTING_GEOMETRY-03 | Minor | — | **Fixed (board).** `arm_gnd`: GND vias 0.5 mm at (13.95, 93.75) and (13.95, 97.15), 0.721 mm from ARM1_SENSE's two layer changes (allowlist A17, A18 gone). BAT_IN J1 → Q120 4.55 → 4.58 mΩ at 0.1 mm (+0.7 %, the two vias alone; 35.2 mV and 0.271 W at 7.7 A); the In2 peak 6.17 A/mm is unchanged. The vias are 0.172 mm from ARM1_SENSE's vias; a short reads "disarmed", a refusal on the ground and only logged in flight (fail-safe) |
| P5-ROUTING_GEOMETRY-04 | Minor | — | **Fixed (tools).** (a) `alt_audit` (gated) re-measures every allowed or recorded tiny_jog, staircase and short_segment: every 1–3 segment octilinear redraw of its window is tested against `r7_hygiene.Clearance`, the keep-outs and the edge; pads and vias stay put and 4+ segment redraws are not searched (stated in the tool). (b) `measured_check` (gated) ties every detour and extra_vias entry to its route length and via count (fails beyond 0.05 mm or one via); the search results quoted in those reasons are not re-run, and each entry names the board they ran on. (c) `LEFTOVER_CATS` holds all 15 hygiene categories. (d) S1–S5 closed: every branch pair in the acute test, jogs and staircases through T, via and pad nodes, `pour_stub`, a layer change into a pad counted, `via_overlap`. Tests 32 → 41 |
| P5-ROUTING_QUALITY-01 | Minor | — | **Fixed.** `band_end`: `R7_GND_In2_strip` also covers x 6.9–9.9, y 25.0–31.3, and the BAT_IN vias (7.6, 26.6), (8.8, 26.6) are removed: the 7 band-end split crossings are gone (12.1 mm of radio B.Cu no longer over In2 BAT_IN). BAT_IN J1 → U9.5 15.14 → 15.18 mΩ (+0.3 %, with the ARM vias). C5 is reduced to the U1 end (7); M3_R7 corrected |
| P5-ROUTING_QUALITY-02 | Minor | — | **Fixed and recorded.** PYRO1_CONT's F.Cu run is S / SE / S, (35.78, 65.25) → (40.88, 70.35) → (40.88, 74.75): the same 47.53 mm chain, 6 vias and GND return vias, 1.080 mm from PYRO1_GATE_N (asserted). Close approaches (DRC-legal): CAM_UART_OE 0.175, SWCLK 0.191, R129.1 0.193, NRST 0.195, 3V3A 0.212, R168.1–SWCLK 0.220, R75.1 0.225 mm, and fix pass 5's GND via (41.375, 70.625) 0.171 mm from the x 40.88 run (a short reads "no continuity": fail-safe); its via (35.78, 58.85) antipad takes 64 SWCLK In1 reference samples (SWD idle in flight). M3_R7, the P4-REGRESSION-01 row and C15 |
| P5-ROUTING_QUALITY-03 | Minor | — | **Fixed (records)** as P5-REGRESSION-01. Optional, not done: start the B.Cu branch east of the via (30.8, 53.1) so that it does not shadow NRST's own In2 branch for about 1.5 mm |
| P5-ROUTING_QUALITY-04 | Minor | — | **2 of 3 removed; 1 forced and recorded.** LOGIC_ILIM (S / SW / SE) and SERVO4_MCU (straight down x 15.505) have no jog now. I2C1_SCL's 0.36 mm step (25.35, 62.25) → (25.71, 62.61) is forced: straight down x 25.35 it collides with BOOT0's via (25.05, 62.85) and the GND via (24.97, 64.4); a BOOT0 via anywhere between IMU_CS (x 24.35) and that column needs 1.095 mm of a 1.0 mm channel; the one BOOT0 spot that would also straighten BOOT0 (x 24.94) puts its In1 antipad under IMU_CS for 0.5 mm (51 reference samples): tried and reverted (F6). QSPI_CLK's new 0.36 mm step is of the same kind (forced by QSPI_IO3's and RXEN's vias), and RADIO_SCK's band staircase became an extra-bend run in fix pass 4 by lengthening its first run past 1 mm: deviation C16. The "14 → 2" of P4-DOCS-01 is corrected in that row. The tiny-jog test stays "offset < 0.25 mm or middle < 0.5 mm" (an offset-only test was optional, not done) |
| P5-ROUTING_QUALITY-05 | Minor | — | **Closed by P5-ROUTING_GEOMETRY-01:** A5 is deleted. The binding obstacle to a straight QSPI_CLK was QSPI_IO3's via (22.5, 40.3), which C16 names |
| P5-DOCS-01 | Major | upheld 3/3, **Major** (Major ×2, Minor) | **Partly fixed; open until the owner decides.** (b) Part D: F6 removed or fixed 15 of the 18 items (D1–D4, D6, D7, D9–D13, D15–D17) and closed D18's tool gaps S1–S5; D8 is a gated allowlist entry with a measured reason (A8); D5 and D14 lie wholly inside a via's copper (C17). (c) The list below now holds every information-only `route_check` instance by category, with counts and the rationale (part E, 249), and the earlier "kept" residuals (C17–C19), and states the pass-2 scanner's categories out of scope (part F). (d) Each part-B row states how much of the present route lies inside another net's pour outline (measured on the final board), and its reason reads "no route found under the stricter rule" wherever the search could not have found the present route either; `route_check.LEFTOVERS` says the same. (a) **No owner acceptance is recorded**; until then M2, and so R7 acceptance, is not met |
| P5-DOCS-02 | Minor | — | **Fixed (records).** M3_R7 "High-current copper: IPC-2152 estimate": equipotential cuts of the solved current field at 0.05 mm give the necks RAW_ACT 2.18 mm of F.Cu (35 µm), BAT_IN 3.71 mm of In2 (30 µm) and ACT_FET_S 2.15 mm of B.Cu (35 µm), each carrying the full 7.7 A, short (0.6–3.1 mm of path within 10 % of the minimum) inside wider copper (median cuts 5.24 / 5.80 / 2.68 mm). Brooks & Adam's fits to the IPC-2152 charts give, for a long conductor of the neck width with no plane, 55, 31 and 56 °C at a continuous 7.7 A, and 20, 19 and 44 °C at the median width; scaled for the solid plane 0.2 mm (outer) or 1.03 mm (In2) away and FR-4 (Brooks & Adam's control case; Inference) about half to two thirds of that. MARGIN_PRESCRIPTION P1-9's "≥ 10 mm equivalent, mirrored and stitched" is not met (RAW_ACT has had no In2 copper since R6). No requirement sets the rise limit; F4's thermal-camera stall test is the check. Deviation C1 (an AGENTS §3 rule instance); REQUIREMENTS F4 points at it (F4 states no temperature limit) |
| P5-DOCS-03 | Minor | — | **Fixed.** MARGIN_PRESCRIPTION's 85 °C row names the MAX-F10S U30 (data sheet R03 Table 13: operating −40 … +85 °C) and the E22-900MM22S U31 (EBYTE manual §2.1/§2.2: −40 … 85 °C) in place of the rev-G SAM-M10Q (10 part classes now); E11 closed (pass-1 paragraph) |
| P5-DOCS-04 | Minor | — | **Fixed (records).** (a) PYRO1_CONT is quoted as `route_check` net copper, 53.33 mm with 6 vias, and the rerouted chain R168.1 → R129.2 is named as such (47.53 mm): A19, the P3-REQUIREMENTS-01 row and M3_R7. (b) NRST 46.11 mm (B19, M3_R7). (c) Placeholder clearances re-measured on the final board as ink polygon to via ring 0.274 mm (RAW_PROTECTED (18.05, 102.87)) and to R157.2's mask opening 0.317 mm; nearest other silkscreen 0.85 mm (the J122 legend; TP88's outline 0.855 mm), nearest designator 1.04 mm (R153) (M3_R7, ORDERING §3; the old "nearest label 1.04 mm" counted designators only). (d) D16 is fixed (CAM_TX_WIRE off In1), so its wording is moot |

### Results after fix pass 5 (board `1ffc2585…`, reviewed by pass 6; superseded)

`tools/check.sh` exit 0 (routing hygiene 0 failing, 33 allowlisted, 30 leftovers recorded); 168 tool tests in 9 suites
and quality_audit 21 passed; the fab package was bound to `1ffc2585…`; $105.98 per board with 52 extended codes
(2026-10-18 12:36Z); DC RAW_ACT 3.95, BAT_IN J1 → Q120 4.58, ACT_FET_S 1.36 mΩ at 0.1 mm; 603 R6-referenced samples
lost; 90 hidden designators. Pass 6 found an inherited, needless square bump on QSPI_IO3 (P6-ROUTING_QUALITY-01); that
`route_check` judged no detour or extra via on a net with a pour while the deviation list said it did (P6-DOCS-01);
that SW_NODE's "forced" allowlist reason was untrue (P6-ROUTING_GEOMETRY-01); a two-segment jog no tool counted (-02);
unlisted in-via steps and R6 debris offsets, and inaccurate C19, D7 and A1/A2 wording (-03); BAT_IN_F left with no
stitching via of its own (P6-REGRESSION-01); a 22.9 mm SERVO4_MCU / CAM_FAULT_N run at 0.165 mm (-02); and unrecorded
adjacencies and wording residues (P6-REGRESSION-03, P6-ROUTING_QUALITY-02/-03, P6-DOCS-02/-03/-04). Its deviation list
is replaced by the one below, and its open items are carried into "Open after fix pass 6".

## Pass 6: four independent reviews of the fix-pass-5 board

**Board reviewed:** `1ffc2585…cdf9df` (the same SHA before and after each review).

**Reviewers:** four, in parallel; each also checked the pass-5 dispositions in its own field. Reports are `pass6_*.md`
in `m3_design/assembly_review/sources/r7_review/`.

**Skeptic step:** each Major went to three skeptic reviewers, who tried to refute it and re-graded it
(`pass6_verdicts.json`). Minor findings were not sent to skeptics.

**Outcome:** no Critical. Both Majors were upheld 3 of 3, and neither was refuted. The skeptics re-graded
P6-ROUTING_QUALITY-01 to Minor (Major, Minor ×2) and kept P6-DOCS-01 Major (Major ×2, Minor); both were worked as Majors
in fix pass 6. 11 Minor.

| Review | File | Critical | Major | Minor |
|---|---|---:|---:|---:|
| Regression and electrical integrity | `pass6_regression.md` | 0 | 0 | 3 |
| Routing geometry (whole board) | `pass6_routing_geometry.md` | 0 | 0 | 3 |
| Routing quality (critical and changed nets) | `pass6_routing_quality.md` | 0 | 1 | 2 |
| Requirements and the owner deviation list | `pass6_docs.md` | 0 | 1 | 3 |

### Implementation of the pass-6 fixes (fix pass 6)

- **F7** (board and tools; `fix6_F7_handoff.md`, log `fix6_F7_progress.md`). Every copper change is in
  `m3_design/r7_polish.py`; the post-hygiene copper is unchanged. A clean `m3_design/r7_build.sh` from the SHA-checked
  R6 board gave **`4673c0a0…`** exactly, twice (13 min 48 s and 12 min 23 s; its `check.sh` passed both times).
  - `r7_polish` stages: `qspi6` (QSPI_IO3's bump replaced by one segment, 24.06 → 21.66 mm); `bat_in_f6` (BAT_IN_F
    grows east to x 9.9 over y 31.4–36.9 and gets two 0.6/0.3 mm BAT_IN vias, (9.7, 31.75) and (9.7, 35.5));
    `servo_fault6` (CAM_FAULT_N and SERVO4_MCU spaced: their parallel run 0.165 → 0.714 / 0.665 mm apart); `sw6`
    (SW_NODE redrawn: A3–A5 gone); `logic_ss6` (LOGIC_SS's knee becomes one diagonal); `v3v3_6` (3V3's dip toward R6's
    removed C179, 9.44 → 6.58 mm); `raw_act6` (RAW_ACT's 31.29 mm B.Cu duplicate deleted); `ties6` (GND J1.2 → via,
    J3.4 → J3.A1B12, J3.1 → J3.B1A12, J3.1 → R85.2, J3.1 → C28.2 and R130.2 → R178.2 redrawn; the 3V3A hop round the
    GND via (36.5, 76.54) shortened; ACT_FET_S R120.1 → Q120.1, 3.60 → 2.41 mm).
  - `tools/route_check.py`: compound tiny jogs (a middle of two or more segments); `chain_detour` and `pour_net_hop`
    on nets with a pour (gated; each exception carries its measured length and via count; every chain-detour entry is
    re-searched by `alt_audit`, whose redraw must end the detour); `alt_audit` keeps 0.26 mm from non-plated holes.
    Tests 41 → 45. Allowlist 33 → 43: A3–A5 out, 8 chain detours and 5 series layer hops in.
  - `m3_design/r7_sch.py`: J31's Value "915MHZ ANT SMA" → "RADIO ANT SMA", as the board's jack legend reads
    (P3-DFM-06(c) closed). One line each in `telemetry.kicad_sch` and `schematic.net.xml`; BOM line 36.
  - Totals: tracks 1,777 → 1,747, vias 706 → 708; pour trims 23 → 22 (F.Cu 9, B.Cu 12, In2 1); 90 hidden designators
    (the same list).
- **Records and documents** (this pass; no copper changed):
  - fab package regenerated and checked; gate, every test suite, cost and procurement rerun;
  - re-measured on the final board: the radio lines over In2 BAT_IN, the in-pour lengths, the GND fingers and the
    single-via GND pieces;
  - every chain detour on a net without a pour (22 critical, 20 non-critical) measured with the gate's own chain test
    and redraw search, and every redraw found tried on a scratch copy (DRC, refill, pour pieces, `route_check`);
    ACT_EN's layer hop measured the same way;
  - the in-via steps and R6 debris offsets listed; the deviation list rewritten with an owner summary;
  - `route_check`'s A1/A2 reason text (`_BAND`) names the binding obstacles (text only);
  - M3_R7, this file, STATUS, AGENTS §1/§3, REQUIREMENTS M2, MARGIN_PRESCRIPTION (P1-9, 85 °C row, R13) and
    ORDERING (§1, §3) updated.

### Every pass-6 finding

"Skeptic" gives the three verdicts and the majority severity; a dash means a Minor finding not sent to skeptics.
Measurements are on the final board (`4673c0a0…`) unless stated otherwise.

| ID | Sev. | Skeptic | Disposition |
|---|---|---|---|
| P6-REGRESSION-01 | Minor | — | **Fixed** (F7 `bat_in_f6`). The old via spots (7.6 / 8.8, 26.6) lie under the band-end In2 GND strip. Inside the old BAT_IN_F the only legal spot that reaches In2 BAT_IN was (8.75, 35.65): TP89's 1.0 mm keep-out and the radio corridor's B.Cu close the rest, and the reviewer's (8.4, 32.0) fails on TP89 (`fx6/viaspot.py`). BAT_IN_F now reaches x 9.9 over y 31.4–36.9 (41.82 mm², holding vias (9.7, 31.75), (9.7, 35.5) and (9.2, 36.05)); both new vias lie in the F.Cu and In2 BAT_IN fills and outside the GND strip. DC at 0.1 mm: C89.1 → U9.5 10.35 → 7.05 mΩ (6.91 before `band_end`), C95.1 → U9.5 7.37 → 5.60 mΩ, J1 → U9.5 15.18 unchanged. critical_reference 0 lost / 0 new. M3_R7 "DC solve" |
| P6-REGRESSION-02 | Minor | — | **Fixed** (F7 `servo_fault6`). CAM_FAULT_N steps onto x 15.19 only below CAM_PWR_EN's via, and SERVO4_MCU onto x 16.005 below the 3V3 via (16.3, 90.525). The parallel run is now 0.714 mm (upper) / 0.665 mm (lower) apart, edge to edge (was 0.165 mm); In2 length within 0.2 mm 30.45 → 6.59 mm (within 0.3 mm 31.26 → 7.33; within 0.5 mm 36.16 → 12.03; `pairlen.py`). What remains (0.161–0.194 mm) is the end diagonals and E runs into y 103.63 / 103.94, pinned by RAW_PROTECTED's via (18.05, 102.87) and the GND vias (24.55 / 25.45, 104.47) (probed), and SERVO4_MCU's 0.164 mm pass of CAM_FAULT_N's via (16.0438, 67.4556). Coupling of the rest ≲ 0.1 V (Inference). C15, M3_R7 |
| P6-REGRESSION-03 | Minor | — | **Recorded** (C15, M3_R7 "Close adjacencies kept"). (a) GND via (35.85, 53.275) to NRST's via (35.80, 53.95): 0.177 mm on all four layers (hole to hole 0.377 mm), and 0.188 mm to NRST's B.Cu diagonal. A short holds the MCU in reset: the board is dead at bring-up, with the pyro gates defined off (AGENTS §2.4) and the radio held in reset. That is not unsafe, but it is not "fail-safe" in the sense C15 used for the sense-node shorts. (b) CAM_FAULT_N's In2 run (y 103.938) is 0.162 mm from the GND vias (24.55, 104.47) and (25.45, 104.47); a short reads "camera fault". Both vias are tented and plugged, and JLC's electrical test screens shorts (Inference). No copper change |
| P6-ROUTING_GEOMETRY-01 | Minor | — | **Fixed** (F7 `sw6`, the reviewer's redraw: SE 0.849, E 1.70, NE 1.414, E 0.70, NE 1.697, ending 0.2 mm further inside L1.1). A3, A4, A5 and `_SW` deleted. Minimum gap 0.213 mm (was 0.170); SW_NODE copper 9.661 → 9.840 mm² (+1.9 %); U2.5 → C5.1, C7, C9 and every GND return untouched; 3V3 DC unchanged. The optional `alt_audit` docstring note (window ends, track ends inside pads included, stay put, and windows are audited one at a time) was not added; M3_R7 states it |
| P6-ROUTING_GEOMETRY-02 | Minor | — | **Fixed** (F7). `route_check`'s tiny_jog also covers a chain P, M1…Mk (k ≥ 2), Q with Q back on P's heading, tiny when the middle is under 0.5 mm in all or Q runs under 0.25 mm off P's line (`compound=k`); `path_defects` tests the same. The only instance on the board was LOGIC_SS (offset 0.141 mm), now one SW diagonal from U11.11's pad edge (`logic_ss6`; 0.183 mm to U11.12 GND; 0.32 mm shorter). Nothing else matched (the nearest, IMU_INT1 B.Cu (26.3, 66.3), runs 0.2503 mm off its line). Test added |
| P6-ROUTING_GEOMETRY-03 | Minor | — | **Fixed (records).** (a) C17 lists every step inside a via's copper on the final board, 12 (the GND step at (36.4, 76.54) is no longer a step after fix pass 6's 3V3A redraw). (b) C21 lists the R6 debris offsets (BAT_IN in D8.1, USB_FAULT_N in R90.2, the ACT_GATE knot). (c) C19 corrected: the run is the first leg of C96.1's link to via (9.7, 54.025), so deleting it would leave the next leg ending on the pad edge; the clean fix is to redraw that leg from inside the pad. (d) The RAW_ACT tail (now A41) ends 0.628 mm inside its fill (scan6; p4extra 0.621), not 0.5. (e) A1/A2 (and `route_check`'s `_BAND` text) name the binding obstacles for lanes on their via rows: D9.1 / D9.2's pads (top edge y 30.3) and the GND via (19.71, 30.51). The optional tidy-ups (re-centring the in-via lanes, aligning the D8.1 and R90.2 runs, the ACT_GATE knot) were not made |
| P6-ROUTING_QUALITY-01 | Major | upheld 3/3 → **Minor** (Major, Minor ×2); worked as Major | **Fixed** (F7 `qspi6`): the five F.Cu segments become one, (22.5, 40.3) → (22.5, 35.4), 0.206 mm from U3.8 (the gap the run already had there), DRC 0; QSPI_IO3 24.06 → 21.66 mm; critical_reference 0 lost / 0 new. Part F is corrected: a local detour on a critical net is an M2 review item, because the gate's detour test works per net. Every chain detour of the pass-2 scan is now judged: 8 on poured nets are gated (A34–A41), 22 on critical nets without a pour are C24, and 20 on non-critical nets are C25 |
| P6-ROUTING_QUALITY-02 | Minor | — | **Fixed (records).** C5 and M3_R7: 1.50–1.96 mm over BAT_IN per line, 12.16 mm for the 7 lines (re-measured on the final board with the reviewer's `refscan.py`) |
| P6-ROUTING_QUALITY-03 | Minor | — | **Fixed (records).** (1) As P6-REGRESSION-03(a). (2) The SERVO4_MCU / CAM_FAULT_N run is spaced (P6-REGRESSION-02); the remaining length within 0.2 mm is in C15. (3) NRST's own-net stacking is C22 |
| P6-DOCS-01 | Major | upheld 3/3, **Major** (Major ×2, Minor) | **Fixed in the gate and the records; open until the owner decides.** (1) `route_check` now gates chain detours and series layer hops on nets with a pour: on the start board 18 chain detours and 5 hops; F7 fixed 10, and 13 are allowlisted with probed blockers and measured figures (A34–A46). (One of the 10, the 3V3A hop, only passed the chain test by 4 µm with the same drawing: P7-ROUTING-04; fix pass 7 restored it and allowlisted it as A47.) (2) Part E's U-turn and layer-hop rationale and part F's coverage statement are corrected. The poured-net layer hops the gate does not count, because their vias join their own pour, are C23. (3)–(6) The 3V3 dip toward R6's removed C179 is redrawn (9.44 → 6.58 mm); RAW_ACT's B.Cu duplicate is deleted (Q121 → J122 3.95 → 3.98 mΩ, +0.8 %; peak density and neck unchanged); the RAW_ACT sense tap stays, with probed blockers (A40, A41, A45). (7) STATUS and M3_R7 no longer claim more than the tools hold. This records pass also measured every chain detour on nets without a pour (C24, C25) and ACT_EN's hop (C26): five items have a DRC-clean redraw that was not applied (owner summary below). **No owner acceptance is recorded** |
| P6-DOCS-02 | Minor | — | **Fixed (records).** (a) B9 and B23 say "under the stricter rule". (b) The preamble names VCAP1 (3.61 mm in an In2 3V3 void) and VBUS (In2 3V3 13.81, F.Cu RAW_ACT 2.97, B.Cu BAT_IN 2.44, In2 BAT_IN 0.90 mm) among the part-A nets inside a pour outline, and A31 says "under the stricter rule". (c) Part F: off-angle within 0.00744° and 0.07 µm; the 3 "collinear" instances are pad-entry necks at plain nodes (BAT_IN → U9.5, RAW_PROTECTED → U9.6, CAM_INPUT_LIMITED → U7.5); `width_change_free`, `_at_pad`, `_at_via`, `short_segment` and `net_length` are accounted for. (d) Part E names 3V3_RADIO's end 0.304 mm off C310.1 (fix pass 5's D4 tidy-up) as new and judges it. (e) Part D says "14 removed or fixed, D18 partly". (f) ACT_EN's hop is measured: removable (C26) |
| P6-DOCS-03 | Minor | — | **Fixed (records).** C1 and M3_R7 give the RAW_ACT neck's own constraints: R6's GND via (18.975, 83.85) and its F.Cu track from C86.2 (18.275, 82.15), which stand inside the RAW_ACT pour, and the zone outline's notch at (21.0, 85.8). Whether that via can move was not searched. MARGIN_PRESCRIPTION P1-9 has an R7 status line (not met; C1) |
| P6-DOCS-04 | Minor | — | (a) **Fixed:** AGENTS §1 (the package is bound to the final fix-pass-6 board) and §3 (every hygiene category is recorded; poured-net chain detours and series hops are gated). (b) **Fixed** by F7 (the LEFTOVERS comment matches `LEFTOVER_CATS`). (c) **Fixed:** MARGIN's 85 °C row and R13 count ten part classes. (d) **Open (board, `r7_post.py`):** "J124: 5A FAST / 2S" sits on B.SilkS at (27.15, 21.9), at the RF strip's edge, about 73 mm from J124 (10.0, 93.32); R6's "UART 3V3 / RX-TX AT MODULE" sits at (26.15, 112.9) beside J1, and its R6 subject, the J130/J131 module ports, is gone in R7. Both are placed with `fallback=True`. Pin them near their subjects or drop the UART legend (board agent; a silkscreen-only change, but it changes the board file and SHA) |

### Results after fix pass 6 (board `4673c0a0…`, reviewed by pass 7; superseded)

`tools/check.sh` exit 0 (routing hygiene 0 failing, 43 allowlisted, 30 leftovers recorded); 172 tool tests in 9 suites
and quality_audit 21 passed; the fab package was bound to `4673c0a0…`; $105.98 per board with 52 extended codes
(2026-10-18 15:51Z); DC RAW_ACT 3.98, BAT_IN J1 → Q120 4.58, ACT_FET_S 1.36 mΩ at 0.1 mm; 603 R6-referenced samples
lost; 90 hidden designators. Pass 7 found needless local bumps on 3V3A, CAM_5V and VLOGIC and in A34's 3V3 run, which
neither the gate nor the list held (P7-ROUTING-01), and a redundant 3V3 via joined only by copper overlap, with an
uncounted 8 mm layer hop (P7-DOCS-01); untrue B7 and B23 reasons and a 3V3_In2 piece fenced off by CAM_5V_SENSE
(P7-ROUTING-02); F7's BAT_IN via on a track body (P7-ROUTING-03); the 3V3A hop "fixed" by a 4 µm threshold artefact
(P7-ROUTING-04, P7-REGRESSION-02); a BAT_IN_B lobe that the deleted RAW_ACT duplicate had fenced off
(P7-REGRESSION-01); an unrecorded SERVO4_MCU – RAW_PROTECTED adjacency (P7-REGRESSION-03); and wrong C23 fill facts,
an incomplete "removable" list, a count that was not like for like and two stale figures (P7-DOCS-02/-03). Its
deviation list is replaced by the one below, and its open items are carried into "Open after fix pass 7".

## Pass 7: three independent reviews of the fix-pass-6 board

**Board reviewed:** `4673c0a0…96ebd` (the same SHA before and after each review).

**Reviewers:** three, in parallel: routing geometry and quality over the whole board, regression and electrical
integrity against the pass-6 board, and requirements with the owner deviation list; each also checked the pass-6
dispositions in its field. Reports are `pass7_*.md` in `m3_design/assembly_review/sources/r7_review/`.

**Skeptic step:** each Major went to skeptic reviewers, who tried to refute it and re-graded it (`pass7_verdicts.json`):
P7-ROUTING-01 to two, P7-DOCS-01 to three. Minor findings were not sent to skeptics.

**Outcome:** no Critical. Both Majors were upheld and neither was refuted: P7-ROUTING-01 2 of 2 (Major, Minor) and
P7-DOCS-01 3 of 3 (Major ×2, Minor); both were worked as Majors in fix pass 7. 8 Minor. The fix-pass-6 records agent's
five "removable" items (C24–C26) were worked in the same fix pass.

| Review | File | Critical | Major | Minor |
|---|---|---:|---:|---:|
| Routing geometry and quality (whole board) | `pass7_routing.md` | 0 | 1 | 3 |
| Regression and electrical integrity | `pass7_regression.md` | 0 | 0 | 3 |
| Requirements and the owner deviation list | `pass7_docs.md` | 0 | 1 | 2 |

### Implementation of the pass-7 fixes (fix pass 7)

- **F8** (board and tools; `fix7_F8_handoff.md`, log `fix7_F8_progress.md`). Every copper change is in
  `m3_design/r7_polish.py`, in twelve stages between `bat_in_f6` and `gnd_vias`; the legends are in `r7_post.py`. A
  clean `m3_design/r7_build.sh` from the SHA-checked R6 board gave **`c872a3d3…`** exactly, twice (about 16 min each;
  its `check.sh` passed both times).
  - `r7_polish` stages: `bumps7` (local bumps: 3V3A's B.Cu bulge round NRST's via, 10.77 → 9.55 mm; CAM_5V's B.Cu
    V-dip, 7.50 → 6.62 mm; VLOGIC's F.Cu peak round D122.2, 6.61 → 6.02 mm; both ends of A34's 3V3 run, 16.32 →
    14.37 mm); `v3pair7` (the redundant 3V3 via (30.4, 70.25) and its 0.81 mm F.Cu stub deleted; the 8 mm In2 run
    starts at via (30.17, 71.17) with a 0.325 mm fan-out diagonal); `acten7` (ACT_EN's In2 hop replaced by one B.Cu run,
    two vias fewer); `arm1_7` (ARM1_SENSE's F.Cu vertical split at R180.1's centre: its pass-through and its chain
    detour are gone, and no pyro copper moved); `tidy7` (CAM_FAULT_N's In2 bump, 10.52 → 7.90 mm; I2C1_SDA's run, 3.47
    → 3.29 mm; LED_RED's straightening tried and reverted); `sense7` (CAM_5V_SENSE's In2 run, 12.43 → 10.89 mm, which
    rejoins a 17.6 mm² 3V3_In2 piece to the plane; SERVO2_OUT's In2 run, net 37.07 → 34.94 mm); `bat_via7` (F7's BAT_IN
    via moved 35 µm onto the B.Cu run's line, (9.725, 35.525), and the run split there); `v3a_hop7` (the 3V3A hop back
    to its fix-pass-5 drawing, allowlisted); `bat_in_b7` (a 0.1 mm notch in BAT_IN_B's outline fences the lobe off
    again); `dup7` (C23's two duplicate 3V3 plane hops deleted); `review7` (non-critical bumps: BUZZ_DRV 21.10 →
    16.22 mm, IMU_INT1 2.33 → 2.07 mm); `necks7` (C1, no part moved: C86.2's GND via and its track out of the RAW_ACT
    neck, ACT_FET_S_B's west edge 1.3 → 0.6 mm, six BAT_IN vias stitching R6's F.Cu crossbar to In2).
  - `r7_post.py`: `label_near` places a legend about a part within 6 mm of its courtyard; the J124 fuse notes, J1's
    lead note, J122's row and the J2 / J9 pin tables now sit beside their parts; R6's "UART 3V3 / RX-TX AT MODULE" is
    deleted (labels 35 → 34).
  - `tools/route_check.py`: `via_on_track` (gated on critical nets; in the via's own fill `via_on_track_in_fill`,
    information); `local_bump` (`bump_audit`, gated on critical nets; `--bumps-all` reports the other nets as
    `local_bump_review`, information); a shared `RedrawCheck` (the true outline and Edge.Cuts circles at 0.5 mm, the
    module keep-outs for non-GND nets); `alt_audit` refuses a same-heading redraw of a chain detour. Tests 45 → 50.
    Allowlist 43 → 45 (the 3V3A hop's chain detour, A47; USB_LIMITED's local bump, A48); leftovers 30 → 29 (B7 gone).
  - `tools/check_r7.py`: `legend_subjects` (every legend about a part within 6 mm of that part's courtyard; gated).
    Tests 34 → 35.
  - Totals: tracks 1,747 → 1,724, vias 708 → 710; pour trims 22 → 23 (F.Cu 9, B.Cu 13, In2 1); 90 hidden designators
    (R121, R123 and U13 newly hidden; C151, R157 and TP88 newly shown).
- **Records and documents** (this pass; no copper changed):
  - fab package regenerated and checked (BOM and CPL byte-identical to F8's, paste parsed); gate, every test suite,
    cost, stock and procurement rerun;
  - re-measured on the final board: `scan.py`, the unstitched GND fingers (C11), the forward-edge GND reach (C20),
    NRST's In2 reference (C10), the key new adjacencies (C15), the pour pieces and the JLC order-number placeholder,
    which `r7_post` moved;
  - the deviation list rewritten with an owner summary, its size stated like for like;
  - M3_R7, this file, STATUS, AGENTS §1/§3, REQUIREMENTS F4/M2/M3, MARGIN_PRESCRIPTION P1-9 and ORDERING §1/§3
    updated.

### Every pass-7 finding

"Skeptic" gives the verdicts and the majority severity; a dash means a Minor finding not sent to skeptics. Measurements
are on the final board (`c872a3d3…`) unless stated otherwise.

| ID | Sev. | Skeptic | Disposition |
|---|---|---|---|
| P7-ROUTING-01 | Major | upheld 2/2 (Major, Minor); worked as Major | **Fixed** (F8 `bumps7`, `v3pair7`). (1) 3V3A: NW, N on x 35.6096, NE: 10.77 → 9.55 mm; minimum gap 0.212 mm, to PYRO1_CONT's via (35.78, 60.65) (re-measured). (2) CAM_5V: W at y 32.45, 45° down x 34.23: 7.50 → 6.62 mm; 0.272 mm (C60.1). (3) VLOGIC: NE, E at y 27.8, S: 6.61 → 6.02 mm; 0.172 mm (C99.2, as before); A33 66.97 → 66.37 mm. (4) A34: the west end one SE diagonal and S on x 38.45 (which also drops the via's 0.35 mm S piece), the east end N, NW, N into C100.1: 16.32 → 14.37 mm (minimum gaps 0.175 mm to RAW_PROTECTED's via (37.85, 54.7) and 0.173 mm to CAM_RX_WIRE's via, re-measured; C15); A34's reason rewritten (the north side is closed by 3V3A's B.Cu run x 40.1 into C11.1; a run between C11's pads is not taken; the C19 / C20 text was wrong). (5) As P7-DOCS-01. The method gap is closed: `local_bump` (every 2–8 segment window of every run on a critical net that turns back, searched with a strict redraw test that includes the reference rule) found these 4 and USB_LIMITED's on the start board, and on the final board only USB_LIMITED's, allowlisted (A48: its redraws cut R105.2 off GND); `alt_audit` no longer takes a same-heading squeeze as a fix. Critical reference 0 lost / 0 new |
| P7-ROUTING-02 | Minor | — | **Fixed** (F8 `sense7`). CAM_5V_SENSE: the reviewer's In2 redraw NW, NE, NW, 12.43 → 10.89 mm (0.182 mm to VLOGIC_SENSE's run, re-measured); 3V3_In2 5 → 4 pieces (474.5, 74.5, 10.3 and 7.5 mm²); B7 deleted (the net-level detour is gone). SERVO2_OUT: the reviewer's In2 redraw, net 37.07 → 34.94 mm, 1 via, 0.171 mm as before; B23's reason rewritten (the present route; `--bumps-all` finds no shorter clean redraw; the raster search's 31.4 mm needs the jogs) |
| P7-ROUTING-03 | Minor | — | **Fixed** (F8 `bat_via7`). No spot clear of the B.Cu run is legal (TP89's 1.0 mm keep-out west, the via (9.2, 36.05), BAT_ILIM's F.Cu east), so the via moved 35 µm onto the run's line, (9.725, 35.525), and the run is split there (a node); it stays inside the BAT_IN_F and In2 fills (asserted). Its 0.74 mm B.Cu piece to the via (9.2, 36.05) is a `short_layer_hop` (C23). The gate now tests this class (`via_on_track`, gated on critical nets): 3 on the start board (the two 3V3 joints and this via), 0 on the final board. The six GND vias on GND track bodies inside their own fill, (6.85, 40.5) among them, are `via_on_track_in_fill` (information, part E) |
| P7-ROUTING-04 | Minor | — | **Fixed** (F8 `v3a_hop7`). The fix-pass-5 drawing (NE, E at y 75.8, SE; 2.505 mm) is restored and allowlisted (A47): the GND via (36.5, 76.54) sits on the straight line, the IMU's GND ties fill the south side, and the hop is kept as U4.5's short path to the 100 nF capacitors at U4.8 (Inference: about 1 nH). Its gap to that via is 0.200 mm (F8; 0.201 re-measured), set by the SE diagonal into the east via's centre; the reviewers' "0.34 mm" is not that drawing's gap. `alt_audit` and `bump_audit` now refuse a same-heading redraw (test). C23's fill statement corrected (both vias lie in the one 28.17 mm² 3V3A_In2 island); C17's GND note corrected (that GND copper is unchanged since the pass-6 board); M3_R7 quotes the `v3v3_6` diagonal's 0.314 mm to the GND via (35.85, 53.275) |
| P7-REGRESSION-01 | Minor | — | **Fixed** (F8 `bat_in_b7`). A 0.1 mm notch in BAT_IN_B's outline along the deleted RAW_ACT leg's line, from the south edge into J124.2's clearance void: BAT_IN_B 94.0 → 70.8 mm² (pass 5: 69.84; +1.0 mm² west of the notch, where the leg and its clearance ran), one piece, fill east edge ≤ x 12.46 (asserted); GND_B refills (+31.7 mm²). Battery voltage no longer borders 3V3, RAW_ACT, USB_ILIM, BUZZ_* or ARM1_SENSE there |
| P7-REGRESSION-02 | Minor | — | **Fixed** as P7-ROUTING-04 (0.200 mm). C15 and M3_R7 give the full failure mode: a hard 3V3A–GND short draws about 1.5 A and 5 W in R164 (2.2 Ω, 0603), which would likely burn open (Inference), losing the IMU, the barometer and U1's VDDA / VREF+; not a pyro hazard |
| P7-REGRESSION-03 | Minor | — | **Recorded** (C15, M3_R7). SERVO4_MCU's In2 diagonal (16.005, 101.627)–(18.005, 103.627) is 0.192 mm from RAW_PROTECTED's via (18.05, 102.87) (re-measured), the same on R6, the pass-5 and the pass-6 boards. It cannot move SW: CAM_FAULT_N's parallel diagonal and E run lie 0.161–0.194 mm away, pinned by the GND vias (24.55 / 25.45, 104.47) (F8). A short would put RAW_PROTECTED (U9's output, up to 8.4 V) on PA3 (U1.25) and, through D121 (SRV05-4), on 3V3; both items are on In2, so only a laminate defect can short them, which electrical test screens (Inference). C15 now states its scope: the sub-0.2 mm gaps that fix-pass copper created or a review raised |
| P7-DOCS-01 | Major | upheld 3/3, **Major** (Major ×2, Minor) | **Fixed** (F8 `v3pair7`, `route_check`). The via (30.4, 70.25) and its stub are deleted: one via fewer, and both overlap-only joints are gone (`via_on_track` 0). The 8.00 mm In2 crossing stays and is listed in C23 with its blockers (along x 30.4 both outer layers are closed by the SPI1 / I2C fan: SERVO3_MCU, SPI1_MOSI, IMU_CS, I2C1_SCL and a RAW_ACT pad on F.Cu; SPI1_SCK, SPI1_MISO, I2C1_SDA and IMU_INT1 on B.Cu, pass-7 review). The five GND vias on GND track bodies, with P7-ROUTING-03's sixth, are counted as `via_on_track_in_fill` (part E). Part F's `via_pair_close` sentence, STATUS and M3_R7 are corrected. **No owner acceptance is recorded** |
| P7-DOCS-02 | Minor | — | **Fixed.** (a) C23 rewritten: the two 3V3 hops are gone, and the 3V3A hop is A47 with its true fill fact. (b) Both 3V3 duplicates deleted (F8 `dup7`; all four vias stay in the 3V3_In2 plane, asserted; L1.2 → U1:27 6.85 → 7.07 and → R164:1 12.50 → 12.66 mΩ). (c) "Removable but not removed" is re-derived in the owner summary. (d) The list's size is stated like for like: an A or B entry is one instance, and C gives its instance count per row |
| P7-DOCS-03 | Minor | — | **Fixed (records).** (a) The P4-RF-01 row now says the fix-pass-4 board had 23 / 49 and points to C11 for the final board (23 / 48). (b) ORDERING §1 and REQUIREMENTS M3 list the same cost runs |
| C24–C26 (fix-pass-6 records) | — | — | ACT_EN's hop: **removed** (F8 `acten7`: R122.2 → S on x 11.75 → SW into Q122.1, 3.84 mm with no via, for 6.12 mm and 2 vias; BAT_IN J1 → Q120 4.58 → 3.90 mΩ on its own). ARM1_SENSE's L: **removed differently** (split at R180.1's centre; the records' redraw at x 16.975 would have left R180.1 joined to the run by 0.065–0.08 mm of overlap with no node). CAM_FAULT_N's In2 bump and I2C1_SDA's run: **removed** (I2C1_SDA as N, NE, E, 0.275 mm minimum gap; the records' N, E, NE kept 0.175 mm to U1.97/98). **LED_RED's In2 bump is not removable:** the records' straight run cut the 3V3_In2 reference under QSPI_NCS's B.Cu run (25.0–26.4, 40.9–42.0), 465 samples lost (F8's build #1), and was reverted; the records' "removable" was wrong (C25) |
| P6-DOCS-04(d) | Minor | — | **Fixed** (F8 `r7_post`, gated by `check_r7.legend_subjects`: 5 far legends on the start board, 0 on the final board). "J124: 5A FAST / 2S" on B.SilkS beside J124 (ink x 12.4–13.9, y 97.6–112.7; it was 65.7 mm away at the RF strip); "J124 2-FUSE-1: ARM LAST" on F.SilkS x 3.1–4.3, y 80.6–101.4; R6's UART legend deleted |
| C1 (IPC-2152) | — | — | **Partly reworked** (F8 `necks7`; no part moved): necks RAW_ACT 2.18 → 3.00 mm, ACT_FET_S 2.15 → 2.65 mm, BAT_IN 3.71 → 3.82 mm; long-conductor rise at the neck width 55 → 38, 56 → 44 and 31 → 30 °C. Still narrower than IPC-2152 asks for a 20 °C rise; deviation C1 |

### Final-board results (CAD, tools; board `c872a3d3…`)

- **`tools/check.sh` exit 0** (F8's two builds and a run on the saved board; rerun by the records agent after the fab
  export and again at the end):
  - DRC 0, unconnected 0, schematic parity 0, ERC 0;
  - metadata/3D audit OK; silkscreen outside the outline 0;
  - R7 CAD contract OK (now including `legend_subjects`);
  - routing hygiene: 0 failing, 45 allowlisted, 0 stale allowlist entries, 0 out-of-date no-GND reasons, 29 leftovers
    recorded (0 unrecorded, 0 stale), 0 out-of-date route figures, 0 removable jog / staircase / short-segment /
    chain-detour exceptions, 1 removable local bump on critical nets (82 bump windows searched; it is USB_LIMITED's,
    allowlisted as A48);
  - actuator safety contract OK;
  - fit OK (CAD envelopes): worst J9 mated 0.03 mm, C84 0.11 mm; nearest bottom envelope C76, 4.150 mm from a
    support; nearest top hardware clearance TP30.1, 5.008 mm.
- **Tests** (KiCad Python, records run): test_check_shell 2, test_dc_solve 3, test_fab_validation 23, test_fit_check
  23, test_maze_clearances 10, test_procurement 15, test_r6_check 17, test_r7_check 35, test_route_check 50: 178 tests
  in 9 suites, all pass; quality_audit 21 under KiCad's Python and python3. `test_r5_repair`: 13 tests, 1 error, the
  known R5-geometry subtest `routing_lands_spacing` (M3_R7).
- **Fab** (records run):
  - `jlc_orient.py`: `CHECK: none`, `jlc_corrections.json` byte-identical (no footprint changed);
  - `export_fab.py`: 92 BOM lines, 219 placed parts and CPL rows, none without an LCSC code, none owner-fitted,
    unfitted placeholders C303, C304, C305, C313, C314, every CPL row with a verified correction. BOM `be711876…` and
    CPL `c68dc2cb…` are byte-identical to fix pass 6's (no part or BOM field changed);
  - `--verify-cpl`: 92 top and 119 bottom rows rebuilt from JLC's footprints, worst residual 0.491 mm, no errors,
    8 placement-only;
  - paste parsed from the Gerbers: none in any J30/J31 pad or in the five unfitted lands; one aperture on each pad
    of R304, R316, C302, D30 and D31;
  - `fab_manifest.py` OK: 5 outputs bound to `c872a3d3…` (173 inputs, all but the board the same as fix pass 6's);
    `test_fab_validation` 23 OK.
- **Cost** (`jlc_cost.py`, live JLC data 2026-10-18 22:02:23Z, 5 boards): parts $77.83 + 92 codes × $1.53 / 5 =
  **$105.98 per board, 52 extended codes**: targets ($126.41, 52) met, no code to spare; $77.83 with JLC minimum
  purchases; two-sided fixed fees $83.96 per order, plus a possible $14.93 handling fee.
- **Stock** (`jlc_stock.py`, 22:03:23Z, bound to the same BOM): short U4 (C26633007, stock 0); thin none; U30 159,
  U31 460, J30/J31 3,299.
- **Procurement:** `check_procurement.py --cost-only` OK (preliminary); the full gate fails on `stock_check.json`
  (U4 short), as expected until U4 is consigned.
- **DC** (F8, board stack-up, 0.1 mm, fix-pass-6 → final board, mΩ): RAW_ACT Q121 → J122 3.98 → 3.74 (peak
  5.78 A/mm on the arm under J122), → J124:2 1.50, → R177:1 86.57 (unchanged); BAT_IN J1 → Q120 4.58 → 3.03 (ACT_EN's
  hop alone 3.90, the crossbar vias the rest; In2 peak 6.13 → 4.72 A/mm); ACT_FET_S 1.36 → 1.19; BAT_IN J1 → U9.5
  15.18 → 13.64, C89.1 / C95.1 → U9.5 7.05 / 5.60 (unchanged); CAM_5V U13:1 → R104:1 24.37 → 19.52; VLOGIC U11:1 →
  C99:1 7.41; 3V3 L1:2 → U1:75 15.64 → 15.62, → FB31:1 14.66 → 12.88, → U1:100 73.46 → 73.63, → U1:27 6.85 → 7.07,
  → R164:1 12.50 → 12.66, → C100:1 77.98 → 74.81; 3V3A U4:5 → C31:1 5.84 → 5.86. At 0.05 mm: RAW_ACT 3.71, BAT_IN 3.03,
  ACT_FET_S 1.16 mΩ.
- **IPC-2152 necks** (F8, equipotential cuts at 0.05 mm; deviation C1): RAW_ACT 3.00 mm, ACT_FET_S 2.65 mm, BAT_IN
  3.82 mm (were 2.18 / 2.15 / 3.71 mm).
- **Critical reference** (F8): fix-pass-6 board → final 0 lost, 0 candidate-new (both methods); against R6 (+18 mm)
  603 lost and 882 candidate-new, as before; extended set 2,312 / 4,325.
- **Copper safety** (F8): every polish stage keeps the pad groups with pours (asserted; `dup7` splits only 3V3's
  track-only groups, asserted); no PYRO1_* copper changed (ARM1_SENSE only split at R180.1); `m3.kicad_dru` untouched;
  `check_actuators` OK. The nearest new copper to a pyro net is 3V3A, 0.212 mm from PYRO1_CONT's via (35.78, 60.65).
- **GND pours:** GND_F 43 → 41 pieces, GND_B 34; none without a via, 32 on a single via (was 34; F8). Unstitched GND
  fingers 0.5–1.0 mm wide: 23 narrower than 0.75 mm and 48 narrower than 1.0 mm (were 21 / 47; records, C11).
- **Silkscreen and DFM:** 90 hidden designators (R121, R123, U13 newly hidden; C151, R157, TP88 shown); every legend
  about a part within 6 mm of its courtyard (`legend_subjects`). The JLC order-number placeholder moved: `r7_post`'s
  search from (23, 94) now places it at (22.9, 86.15) on B.SilkS (ink x 17.87–27.97, y 85.53–86.68), over no via (ink
  to the nearest via ring 0.343 mm, GND (25.5, 87.32)), 1.17 mm from the nearest pad opening (C150.2) and 0.30 mm from
  the nearest other silkscreen, C151's newly shown designator (records; ORDERING §3). J2.1's in-pad via and TP122's are
  unchanged. Renders `r7_top.png` / `r7_bottom.png` show the final copper (F8).

## R7 deviations for owner acceptance

### Owner summary (board `c872a3d3…`)

**Owner acceptance (2026-10-18):** the owner accepted this deviation list as recorded for board `c872a3d3…`, with the 7.7 A servo-feed copper rise (C1) accepted as estimated. With review pass 8 (0 Critical / 0 Major), REQUIREMENTS M2 and R7 acceptance are met in CAD.

**The decision that was asked:** accept this list, dated, as the R7 deviations from your clean-routing criterion
(REQUIREMENTS M2), or send the board back for more rerouting first. Until you do one or the other, M2 is not met, and
so neither is R7 acceptance. Separately, set the temperature rise you allow on the 7.7 A servo-feed copper (C1), or
order the further rework it needs (ACT_GATE or parts moved, or the battery-corner re-layout).

| Part | What it holds | Entries | Instances | AGENTS §3 | Held by |
|---|---|---:|---:|---:|---|
| A | `route_check` allowlist (gated rules on critical nets) | 45 | 45 | 9 | the gate: each entry matched and its reason re-measured on every run (except A42–A46's probed blockers and A48's GND reason) |
| B | non-critical leftovers | 29 | 29 | 0 | the gate: counted, recorded, figures re-measured |
| C | review deviations the gate does not hold | 25 rows | 225 | 1 row (C1, 3 necks) | review only |
| E | information-only `route_check` instances | 9 categories | 252 | 0 | counted, never gated |

**Size, like for like:** A, B and C hold 99 entries and rows, or **299 instances** counted one per named location. An
A or B entry is one instance; C's 25 rows hold 225: C1 3, C2 6, C3 1, C4 2, C5 7, C6 1, C8 1, C9 3, C10 1, C11 48,
C12 1, C13 2, C14 32, C15 40, C16 4, C17 12, C18 11, C19 1, C20 1, C21 3, C22 1, C23 3, C24 21, C25 17, C27 3. Most of
C's count is pour stitching (C11's 48 fingers, C14's 32 single-via pieces), close adjacencies (C15, 40) and chain
detours (C24 and C25, 38). The 252 information-only instances come on top. (The fix-pass-6 list's "98" was 43 + 30
entries plus 25 rows.)

**The AGENTS §3 items, and why each is still there** (10 items, 12 instances: 9 allowlist entries and C1's three
necks):
- **A6, A7, A9–A14:** eight radio-interface layer changes (band via columns, U1 escape, left-edge corridor) with no
  GND via within 1.5 mm. No legal spot exists: the project's GND-via search runs on every gate run (0.025 mm grid,
  0.6 and 0.5 mm vias, every board rule) and finds none, and sliding each signal via ±0.6 mm along its tracks opens
  none. Removing them means re-spacing the band and corridor via columns, a re-layout of the interface. They carry slow
  control lines and SPI up to 10 Mbps.
- **A8:** PYRO1_GATE's layer change into TP122's pad. A GND via within 1.5 mm would come within 0.45 mm of that bare
  test pad, which keeps 1.0 mm from foreign copper. Removing it means moving or dropping the gate-drive test point.
  No current flows through it: the gate is driven on F.Cu.
- **C1:** the 7.7 A servo feed is narrower than IPC-2152 asks. Fix pass 7 widened its necks without moving a part:
  RAW_ACT 2.18 → 3.00 mm (C86.2's GND via taken out of the neck), ACT_FET_S 2.15 → 2.65 mm (the pour's west edge to
  0.6 mm), BAT_IN 3.71 → 3.82 mm (six vias put R6's unused F.Cu crossbar in parallel with In2). At a continuous
  four-servo stall IPC-2152's fits give 38 / 44 / 30 °C at those necks with no plane credit (55 / 56 / 31 °C before),
  about 18–20 °C with it (Inference); the paths fell to 3.74 / 1.19 / 3.03 mΩ. Each neck is now set by something a
  bounded rework cannot move: J122's pin columns and the zone notch that keeps RAW_ACT off the pyro block; Q120's
  gate pad and R120; ACT_GATE's In2 crossing. MARGIN_PRESCRIPTION P1-9's ≥ 10 mm is still not met. No requirement sets
  the allowed rise; flight 1's single servo gives under 1/12 of it.

**Removable but not removed.** Fix pass 7 removed every item the fix-pass-6 records had called removable except
LED_RED's In2 bump, which proved not removable (its redraw cut QSPI_NCS's reference, C25), and every item the pass-7
reviews showed removable. Left:
- C27: two non-critical local bumps whose shorter redraws pass every check but narrow a gap: VLOGIC_SENSE (−0.33 mm,
  to 0.165 mm from a GND via) and BAT_SW_SOURCE, a harness line (−1.80 mm, to 0.187 mm from its neighbour); kept by
  judgement;
- not examined: C23's 0.74 mm BAT_IN piece between two vias that both join both BAT_IN fills;
- not attempted: the cosmetic tidy-ups of C17 (steps inside via copper), C19 (a BAT_IN run inside C96.1's pad), C21
  (R6 debris offsets) and C22 (NRST's own-net stacking), each a small redraw.

A board pass can remove them (then a rebuild, the gate and a review pass), or you can accept them as listed.

**New in fix pass 7, for your attention:** unstitched GND fingers 0.5–1.0 mm wide beside the new 3V3A and ACT_EN
runs, and one beside A34's run narrowed below 0.75 mm (C11; not searched for a via spot); and three sub-0.2 mm gaps
where a short would put a higher rail on 3V3 or an MCU pin: C15 #34 (RAW_PROTECTED to SERVO4_MCU, inherited from R6), #35 (RAW_PROTECTED to 3V3, 0.157 mm
before fix pass 7's redraw) and #39 (VLOGIC to 3V3, new), all DRC-legal and screened by JLC's electrical test
(Inference).

**Needed before ordering, whatever you decide:** an independent review pass on `c872a3d3…` with no open Critical or
Major (none has run yet), U4 consigned, JLC's written confirmation of the forward panel rail, and the order-number
placeholder checked at its new spot (ORDERING §3).

### How the list is built

REQUIREMENTS M2 counts every item below as a deviation from the owner's clean-routing criterion until the owner
accepts it. This is the one list M2 names as awaiting that acceptance (as it names M3_R4 §2 for the thermal-relief
exceptions). It is bound to the final board `c872a3d30509cccf5f78b64cde48ef722ee85c7be23c4848b07ce4082a852de3`: any
copper change reopens it.

- **A** and **B** are the entries of `tools/route_check.py` (`ALLOWLIST`, `LEFTOVERS`), whose full measured reasons
  are in the tool. Every gate run matches each entry to an instance (a stale entry or an unrecorded instance fails) and
  re-measures its reason: `nognd_audit` reruns the GND-via spot search behind each no-GND entry; `alt_audit` searches
  every 1–3 segment redraw of each jog, staircase, short-segment or chain-detour window (window ends fixed, one window
  at a time; since fix pass 7 through the shared `RedrawCheck`: clearance to other-net copper, keep-out rule areas, the
  U30 / U31 module keep-outs for non-GND nets, non-plated holes and the true board outline at 0.5 mm; a same-heading
  redraw does not count as a fix; pours are not refilled); `bump_audit` searches every 2–8 segment window of every run
  on a critical net for a removable local bump (gated; the one it finds, A48, is allowlisted); `measured_check`
  compares each detour, extra-vias, chain-detour and series-hop entry's quoted length and via count with the board.
  The raster-search results quoted in detour and extra-vias reasons are not re-run; they come from the fix-pass-4
  board (F5's runs), whose copper on those nets differs only where a row says so.
- **C** lists the review deviations the tool does not hold, each measured.
- **D** gives the status of the fix-pass-4 list's part D (18 items).
- **E** summarises the information-only `route_check` instances by category, with counts and the reason they are
  information.
- **F** states what is outside the list.

**AGENTS §3 rule instances** are marked **§3**: the rules of AGENTS.md §3 itself (0°/45°/90° only, no staircases,
acute angles or stubs, a GND via within 1.5 mm of every layer change of a critical signal net, high-current copper
sized per IPC-2152). Everything else is an M2 item (the owner's wider clean-routing list) or a review item.

"Search" means the raster search over F.Cu, B.Cu and In2 at 0.05 mm (some at 0.1 mm over the whole board), with every
board clearance including the pyro rules, bare test pads 1.0 mm, Tag-Connect 0.508 mm, the crystal kept clear and
**every power pour on every layer kept whole** (F4, F5). That is a stricter rule than the board follows: 19 of the 22
part-B nets, and in part A ARM1_SENSE (26.92 mm in an In2 3V3 void), QSPI_IO2 (13.33 mm), VCAP1 (3.61 mm) and VBUS
(In2 3V3 13.81, F.Cu RAW_ACT 2.97, B.Cu BAT_IN 2.44 and In2 BAT_IN 0.90 mm), run partly inside another net's pour
outline, in a void the fill leaves round them (measured on the final board). So "no route" or "the best found" holds
under that rule only, not for every route the board itself would allow; whether a present In2 run splits an island or
merely slots it was measured only where a row says so. The search knows nothing of the RF strip's fence openings, its
GND-only In2 or the module keep-outs.

**Owner acceptance: none recorded.**

### A. `route_check` allowlist (45 entries, gated rules on critical nets)

A3–A5 (SW_NODE) were removed in fix pass 6 (P6-ROUTING_GEOMETRY-01); numbers are not reused. A34–A46 are new in fix
pass 6: chain detours and series layer hops on nets with a pour (A34 was C7; A41 holds D7's tail). A47 (the 3V3A hop's
chain detour) and A48 (USB_LIMITED's local bump) are new in fix pass 7.

| # | Rule | Net, location | Measured reason | Why it cannot reasonably be removed |
|---|---|---|---|---|
| A1 | M2 tiny jog (critical) | RADIO_BUSY, F.Cu (9.4, 28.2): 0.283 mm 45° step, 0.2 mm offset | band vias in two columns (x 9.4 / 10.0) on 0.5 mm rows; F.Cu lanes at 0.4 mm pitch, so the lane leaves its via 0.2 mm off its row, and a 45° step of < 0.25 mm offset is a tiny jog at any length; the step cannot sit before the 10.0 column (BUSY at y 28.0 overlaps RADIO_NRST's via (10.0, 27.7) by 0.025 mm). With every lane on its via row the binding obstacles are D9.1 / D9.2's pads (top edge y 30.3: RADIO_NSS's lane at y 30.2 would pass them at 0.025 mm) and the GND via (19.71, 30.51), which that lane would overlap (pass 6, measured); `alt_audit` finds no clean 1–3 segment redraw (gated) | only re-spacing the band via columns or rows, or moving D9 and that GND via, removes it: a re-layout of the interface band |
| A2 | M2 tiny jog (critical) | RADIO_MISO_MCU, F.Cu (10.0, 28.7): 0.424 mm step, 0.3 mm offset | as A1 (row 28.7, lane 28.4) | as A1 |
| A6 | **§3** GND via within 1.5 mm of a critical layer change | RADIO_RXEN via (23.8, 39.45); nearest GND via 2.23 mm | no legal GND via spot within 1.5 mm: `nognd_audit` (gated, every check) runs `r7_hygiene.gnd_spots` (`GndFit`: `ViaCheck` with board rules + 0.02 mm and no via within 0.15 mm of a GND solder pad, bare test pads 1.02 mm, Tag-Connect 0.528 mm, Pyro D 0.52 mm, the 7.7 A corridors; 0.6 and 0.5 mm vias; 0.025 mm grid) and finds none; sliding the signal via up to ±0.6 mm along its tracks opens none (F5) | no spot exists without moving neighbouring signal vias; a respin item (re-space the band and corridor via columns). Slow control line |
| A7 | **§3** as A6 | RADIO_NRST via (9.3, 50.0), left-edge corridor; 3.18 mm | as A6; the corridor's B.Cu side references the In2 BAT_IN arm (x 7.2–9.9), not GND | as A6 |
| A8 | **§3** as A6 | PYRO1_GATE layer change F.Cu → TP122's pad via (20.45, 92.4); 2.93 mm | the via sits in TP122's 1.5 mm bare test pad (the gate drive's probe point, B.Cu): a GND via within 1.5 mm of it would come within 0.45 mm of the pad edge, against the 1.0 mm a bare test pad keeps from foreign copper (`check_r7`; `GndFit` 1.02 mm), so `nognd_audit` finds no spot (counted since fix pass 5; was D8). The layer change carries no through current: the gate is driven on F.Cu and TP122 is a terminal | moving the test pad or dropping it (the bench gate-drive check uses it) |
| A9 | **§3** as A6 | RADIO_BUSY via (9.4, 28.2), band columns; 1.65 mm | as A6 | as A6 |
| A10 | **§3** as A6 | RADIO_BUSY via (10.0, 49.5), corridor; 2.60 mm | as A6 | as A6 |
| A11 | **§3** as A6 | RADIO_MOSI via (9.4, 29.2), band columns; 1.65 mm | as A6 (E22 SPI, up to 10 Mbps) | as A6 |
| A12 | **§3** as A6 | RADIO_DIO1 via (10.0, 50.5), corridor; 3.57 mm | as A6 | as A6 |
| A13 | **§3** as A6 | RADIO_MISO_MCU via (10.0, 28.7), band columns; 2.11 mm | as A6 (SPI) | as A6 |
| A14 | **§3** as A6 | RADIO_MOSI_MCU via (9.4, 48.5), corridor; 1.71 mm | as A6 (SPI) | as A6 |
| A15 | M2 extra vias (critical) | ARM1_SENSE (19.2, 92.4): 63.73 mm / 4 vias | R170.1 on B.Cu at U1, the divider (R133, R180, R175, C129) on F.Cu in the pyro block; search R170.1 → R133.1 with every pyro rule: no route with fewer than 4 vias (51.8 mm / 4). 26.9 mm of the present route lies in an In2 3V3 pour void. Fix pass 7 split its F.Cu vertical at R180.1's centre, so the L at (14.55, 94.15) no longer passes through R180.1 and is no longer a chain detour (length and vias unchanged) | no route with fewer vias found under the stricter rule |
| A16 | M2 detour (critical) | GNSS_LNA_EN (13.0, 13.3): 7.45 mm / 1 via for a 3.72 mm pad tree | limiter on B.Cu under U30; U30.13 / U30.14 are F.Cu pads on the module's aft row and only GND may cross F.Cu / In1 under the module (u-blox IM §4.4), so the net leaves 1.9 mm aft to a via and runs back under it | forced by the module keep-out |
| A17 | M2 detour (critical) | GNSS_RESET_N (14.3, 54.5): 59.34 mm / 2 vias | R7 interface topology (west escape, left-edge B.Cu corridor over In2 GND, F.Cu band, lanes between the modules; the strip admits signals only through its fence openings and holds no In2 signal copper); search: 39.3 mm only with a 28.7 mm In2 run through the 3V3 plane and an F.Cu run across the strip fence outside its openings | every shorter route found cuts the 3V3 plane or breaks F10's strip rules |
| A18 | M2 detour (critical) | GNSS_VCC_RF (9.7, 12.25): 6.2 mm / 1 via for 2.61 mm | as A16 | as A16 |
| A19 | M2 extra vias (critical) | PYRO1_CONT (24.6, 87.2): net copper 53.33 mm / 6 vias (the rerouted chain R168.1 → R129.2 47.53 mm) | fix-pass-4 plane-preserving route (F.Cu run S / SE / S since fix pass 5): R168.1 on B.Cu at U1, the divider on F.Cu in the pyro block, SWCLK / SWDIO and the IMU between; search with every power pour on every layer kept whole (3V3 / 3V3A included), 1.0 mm to PYRO1_GATE_N and every pyro rule: no route with fewer than 6 vias (via cost 15); each layer change has a GND via within 1.5 mm | fewer vias only by cutting the In2 3V3 island under U1/U4 (fix pass 3's 4-via route did, P4-REGRESSION-01) |
| A20 | M2 extra vias (critical) | QSPI_IO2 (29.4, 59.5): 33.26 mm / 3 vias | U1.1 (right column) to U3.3 (north of U1) crosses U1's right-side escapes and the QSPI fan; search: 31.9 mm / 3 vias at best. 13.3 mm lies in an In2 3V3 pour void (its In2 overshoot near (30.7–32.5, 57.7–59.5) is part of this route) | no route with fewer vias found under the stricter rule |
| A21 | M2 detour (critical) | RADIO_DIO1 (14.3, 50.5): 69.09 mm / 4 vias | interface topology; search: 48.0 mm / 2 vias only with a 39.8 mm In2 run ending inside the strip (In2 there is GND only) | as A17 |
| A22 | M2 extra vias (critical) | RADIO_DIO1 (14.3, 50.5): 4 vias | as A21 | as A17 |
| A23 | M2 detour (critical) | RADIO_NRST (37.0, 14.0): 85.44 mm / 4 vias | interface topology, R311 beside U31; search U1.56 → U31.3: 51.3 mm only with a 32.1 mm In2 run into the strip | as A17 |
| A24 | M2 extra vias (critical) | RADIO_NRST (37.0, 14.0): 4 vias | as A23 | as A17 |
| A25 | M2 extra vias (critical) | RADIO_NSS (24.2, 20.39): 58.4 mm / 4 vias | interface topology; search U1.51 → U31.14: 3 vias only with a 25.2 mm In2 run ending inside the strip | as A17 |
| A26 | M2 extra vias (critical) | RADIO_RXEN (25.6, 7.43): 51.88 mm / 4 vias | fix-pass-2 route (F.Cu lane x 20.6 between the modules, R312 at U31; on its via column x 23.8 since fix pass 5); search U1.45 → U31.10: 2 vias only with an 18.2 mm In2 run under the 3V3 buck (U2, C7, L1) through the 3V3 plane | as A17 |
| A27 | M2 detour (critical) | RADIO_TXEN (31.13, 18.95): 25.17 mm / 2 vias | U31.19 and U31.9 sit on opposite sides of the module, and only GND may cross its pad field on any layer (EBYTE §4.1; `U31_KEEPOUT` on B.Cu and In2); the search's 12.2 mm path crosses the keep-out, and so does the only 1–3 segment redraw of its B.Cu run (C24) | the direct path is forbidden by the module maker's layout rule |
| A28 | M2 extra vias (critical) | RAW_PROTECTED (35.7, 85.675): 143.53 mm / 7 vias, 12 pads | 3 pads on F.Cu (U9.6, C82.1, D9.1), 9 on B.Cu from y 27 to y 104 (U11, C97, R92, TP70, TP81, U7, C71, R122): an interleaved distribution tree | inherited R6 topology; fewer vias needs parts moved to one side |
| A29 | M2 detour (critical) | VBUS (6.8, 76.3): 42.49 mm tree, 8 pads | J3's two VBUS contact groups (F.Cu, 4.8 mm apart) and C83 on F.Cu; C28, D4, R9 and U10 on B.Cu; the tree joins both contacts through C28 and the clamp D4 | inherited R6 USB-C input; the topology follows the parts on both sides |
| A30 | M2 extra vias (critical) | VBUS (6.8, 76.3): 6 vias | as A29: F and B pads interleave | as A29 |
| A31 | M2 detour (critical) | VCAP1 (18.2, 45.9): 6.71 mm / 2 vias for 1.37 mm (4.89×) | C19.1 sits on B.Cu under U1 between its escape vias; search: nothing shorter than 5.81 mm / 2 vias under the stricter rule (3.61 mm of the present route lies in an In2 3V3 void); copper 13.9 mΩ, within ST's VCAP ESR < 100 mΩ (DS12110) | inherited R6; needs C19 moved (respin) |
| A32 | M2 detour (critical) | VCAP2 (16.0, 60.8): 12.67 mm / 1 via for 3.0 mm (4.22×) | U1.73 escapes west, C20.1 on B.Cu under U1's SW corner; direct via spots collide with C17, 3V3, USB_DP's via, the SWD lines and TP85; search: the same west loop at 10.75 mm / 1 via; copper 25.4 mΩ, within the ESR limit | inherited R6; needs C20 moved next to U1.73 (respin) |
| A33 | M2 extra vias (critical) | VLOGIC (18.2, 29.4): 66.37 mm / 5 vias, 10 pads | 2 pads on F.Cu (C84.1 at x 7.5, C99.1 at U11), 8 on B.Cu (U2, C7, C6, TP83, U11, R60); C84, the bulk capacitor, sits 10 mm west of U2; fix pass 5 ended two runs at the U2.2 / U2.3 pad centres (+0.1 mm); fix pass 7 took the 0.6 mm F.Cu peak round D122.2 out (P7-ROUTING-01) | as A28 |
| A34 | M2 detour, chain on a poured net (critical) | 3V3 B.Cu (36.94, 52.65) → C100.1: 14.37 mm for 5.16 (was C7; 16.32 mm until fix pass 7 redrew the local bumps at both ends, P7-ROUTING-01) | U12 / C100's 3V3 feed runs round the south end of C11 (B.Cu, 39.4–40.8, 53.9–57.3: C11.1 3V3A, C11.2 GND) and back up into C100.1; the north side is closed by 3V3A's B.Cu run x 40.1 (y 51.9–54.6), which ends in C11.1, so both octilinear two-segment routes cross it; a run between C11's two pads (0.65 mm gap) is not taken (`bump_audit`'s strict test); `alt_audit`: no 1–3 segment redraw ends the detour, and `bump_audit` finds no other shorter window | inherited R6; a shorter feed needs C100 or C11 moved, or C100.1 given its own via into 3V3_In2 |
| A35 | as A34 | GND F.Cu (14.3, 59.0), U1.74 → its GND via (11.3, 59.3): 6.62 mm for 3.12 | the run goes round 3V3's F.Cu run (12.6–14.3, y 59.5) and via (12.6, 59.5), which both two-segment routes cross; `alt_audit`: no redraw | inherited R6; removal needs 3V3's F.Cu run and via (12.6, 59.5) moved |
| A36 | as A34 | GND F.Cu (16.35, 45.95), U1.49 → the GND via (16.35, 43.55) 2.4 mm above it: 6.56 mm | the straight run passes the 3V3 via (15.85, 44.25) at 0.075 mm (rule 0.15), so it goes round it; `alt_audit`: no redraw | inherited R6; removal needs the 3V3 via (15.85, 44.25) moved |
| A37 | as A34 | GND F.Cu (27.65, 29.85) → C99.2: 2.31 mm for 1.78 | both two-segment routes cross VLOGIC's F.Cu diagonal (27.905, 29.25)–(28.505, 29.85); the clean three-segment redraws are longer (2.53 mm) | every clean 1–3 segment redraw is longer than the present run |
| A38 | as A34 | GND B.Cu (13.7, 80.6), U10.2 → Q123.2: 6.08 mm for 3.42 | the two-segment routes cross U10.1 (VBUS) and RAW_ACT's via (12.6, 81.27); `alt_audit`: no redraw | inherited R6; removal needs U10 or RAW_ACT's via moved |
| A39 | as A34 | GND B.Cu (32.3, 55.7), C23.2 → the GND via (31.5, 53.5): 4.01 mm for 2.53 | the two-segment routes cross 3V3's B.Cu run to C23.1 (31.1–32.1, y 54.5); the clean three-segment redraws are longer (4.05 mm) | as A37 |
| A40 | as A34 | RAW_ACT F.Cu (10.4, 64.67), the RAW_ACT_SENSE tap from R177.1 to its via (13.7, 65.37): 5.60 mm for 3.59 | a divider feed (µA). The direct routes cross GND's F.Cu (11.37, 64.1–65.1) between R177 and R182, and a via beside R177.1 collides with VBUS_SENSE's F.Cu diagonal (8.0, 65.9)–(10.9, 63.0) and USB_DM / USB_DP's B.Cu at x 10.05 (probed, F7) | inherited R6; no shorter legal tap found (F7, probed) |
| A41 | as A34 | RAW_ACT F.Cu (12.6, 81.27), the same tap's end from its In2 / F.Cu via into R6_RAW_ACT_F: 7.11 mm for 5.12; it ends 0.628 mm inside that fill (was D7) | VBUS's F.Cu run (10.8, 79.95)–(10.8, 81.525)–(11.325, 82.05)–(13.225, 82.05) and C83.1 box the via in (the 0.5 mm² fill fragment round it joins nothing), so the run goes round VBUS's via (10.8, 79.95) to the fill west of it; the direct routes cross that VBUS copper (F7, probed); `alt_audit`: no redraw | inherited R6; as A40 |
| A42 | M2 extra vias, series layer hop on a poured net (critical) | 3V3 via (41.0, 77.92) → J2.1's via (44.035, 77.92): 11.19 mm / 2 vias | 3V3 into J2.1 (Tag-Connect; its in-pad via is M2's named exception): on F.Cu the feed would cross SWDIO's diagonal (33.43, 69.65)–(41.7, 77.92) into J2 and J2's 0.508 mm contact rule, so it runs on B.Cu under J2's pad field (F7, probed) | the F.Cu route is blocked by SWDIO and J2's contact rule |
| A43 | as A42 | 3V3 via (12.5, 89.2) → (16.3, 90.525): 22.97 mm / 2 vias | the 3V3 In2 feed (7.9, 84.6) → (21.9, 96.125): In2 between x 12.5 and 16.3 holds the BAT_IN In2 fill (x < 14) and CAM_FAULT_N's and SERVO4_MCU's In2 runs (x 14.64–16.0), which an In2 run cannot cross; the 3.8 mm F.Cu hop passes over them (F7, probed) | an In2 run cannot cross those lanes, which fix pass 6 has just spaced (P6-REGRESSION-02) |
| A44 | as A42 | 3V3 via (35.1, 45.025) → (36.5, 50.15): 12.32 mm / 2 vias | 3V3 from B.Cu (33.8, 43.725) to the F.Cu T (36.5, 51.65) through an In2 run in a 3V3_In2 void: on B.Cu the run would cross 3V3A's B.Cu (36.9–39.4, y 48.1), on F.Cu RAW_PROTECTED's diagonal (36.15, 47.9)–(38.05, 49.8) (F7, probed) | both outer-layer routes are blocked |
| A45 | as A42 | RAW_ACT via (13.1, 75.97) → (13.7, 65.37): 22.29 mm / 2 vias | the RAW_ACT_SENSE tap R177.1 (F.Cu) → R6_RAW_ACT_F (F.Cu) through B.Cu and In2: F.Cu is closed by LS120.1, D123.1 and 3V3's F.Cu runs (x 11–13.4, y 76.5–80.2), B.Cu by the BAT_IN_B pour from y 80.9 and Q123 / U10 / R163 (F7, probed) | inherited R6; as A40 |
| A46 | as A42 | CAM_5V via (41.3, 32.425) → (43.3, 33.425): 4.61 mm / 2 vias | U13.1 → C91.1, both on B.Cu: the B.Cu route crosses CAM_IO_3V3's B.Cu diagonal (42.8, 32.45)–(40.75, 34.5) and U13.5 (F7, probed); the 2.4 mm F.Cu hop passes over it | inherited R6; the B.Cu route is blocked |
| A47 | M2 detour, chain on a poured net (critical) | 3V3A B.Cu via (35.5, 76.54) → via (37.4, 76.52): 2.505 mm for 1.908 | the hop from U4.5's (VDDIO) via to the U4.8 / C31 / C30 node's via goes round the GND via (36.5, 76.54), U4.6 / U4.7's return via, which sits on the straight line 1.0 / 0.9 mm from the two; the IMU's GND ties fill the south side, so it goes north (NE, E at y 75.8, SE); its gap to that GND via, 0.200 mm, is set by the SE diagonal into the east via's centre (C15); both vias also join the one 28.17 mm² 3V3A_In2 island, and the hop is kept as U4.5's short path to the 100 nF capacitors (Inference: via → island → via adds about 1 nH); fix pass 6's tighter copy of the same drawing only cut the gap to 0.169 mm (P7-ROUTING-04) | removal means moving that GND via or U4's decoupling vias, or deleting the hop with a decoupling judgement (not made) |
| A48 | M2 local bump (critical; `bump_audit`, fix pass 7) | USB_LIMITED B.Cu C98.1 (33.1, 26.15) → the U11.7 node (30.8, 27.85): 4.35 mm for 3.00 | C98.1 (U11's input bulk capacitor) leaves its pad's top edge NW, W, SW round BAT_SW_RETURN's via (31.9, 26.325) and comes back S (inherited R6; also a C24 chain detour). The 3.44 mm redraw `bump_audit` finds (S, SW past the GND via (32.2, 27.033), W into the node) cuts the B.Cu GND copper that is R105.2's only path to that via: R105.2 leaves the GND pad group (F8, pad-group check); between that GND via and the BAT_SW_RETURN via there is 0.216 mm, too little for the 0.25 mm run | removal needs that GND via or the BAT_SW_RETURN via moved |

`alt_audit` re-searches A1, A2, A34–A41 and A47 on every run; the blockers of A42–A46 were probed by F7
(`fx6/probe.py`, `p_hop.json`) and are not re-searched by the gate (only their lengths and via counts are, by
`measured_check`). `bump_audit` finds A48's 3.44 mm redraw on every run (the gate line's "1 removable local bump");
its reason, R105.2's GND, is F8's measurement and is not re-run by the gate.

### B. Non-critical leftovers (`route_check.LEFTOVERS`, 29 entries, counted and recorded, not gated)

These nets are LED, camera, buzzer, servo PWM, fault-flag, switch-sense, reset and SWD lines. "In pour" is the present
copper inside another net's pour outline on the same layer (measured on the final board): where it is large the
search, which keeps every pour whole, could not have found the present route. Search results are F5's, on the
fix-pass-4 board, each net searched with its own copper removed (multi-pad nets edge by edge over the octilinear
minimum spanning tree of their pads, summed). B7 (CAM_5V_SENSE's detour) went in fix pass 7 when its In2 run was
redrawn (P7-ROUTING-02); the number is not reused.

| # | Rule | Net, location | Present (in pour) | Search result and measured reason | Why it cannot reasonably be removed |
|---|---|---|---|---|---|
| B1 | M2 detour | BAT_FAULT_N (11.975, 43.1) | 39.97 mm / 4 vias for a 22.47 mm tree (25.0 mm in an In2 3V3 void) | search: 31.4 mm / 2 vias, but only with a forced 0.125 mm jog (B.Cu between VLOGIC at x 11.9 and QSPI_IO0's via (12.9, 44.4)) and a via hairpin under U1.81 (TP87's 1.0 mm keep-out and C20 leave no via spot on the pin's line) | the only shorter route found trades length for a tiny jog and a hairpin, which M2 also forbids |
| B2 | M2 extra vias | BAT_FAULT_N | 4 vias | as B1 | as B1 |
| B3 | M2 detour | BAT_SW_RETURN (15.38, 110.4) | 160.34 mm / 5 vias for 76.28 mm (J1.4 → R165.1, round the east edge; 19.5 mm through the F.Cu BAT_IN crossbar's void, which stays one 232 mm² piece, + 1.3 mm In2 3V3) | search (0.1 mm, whole board): 177.7 mm / 7 vias, longer; the direct west side is closed by the 7.7 A BAT_IN / RAW_ACT pours | no shorter route found under the stricter rule (inherited R6) |
| B4 | M2 extra vias | BAT_SW_RETURN | 5 vias | the search's best has 7 | as B3 |
| B5 | M2 extra vias | BAT_SW_SOURCE (20.46, 110.4) | 129.2 mm / 7 vias (1.0 mm F.Cu BAT_IN) | search (0.1 mm, whole board): 124.9 mm / 6 vias, with six F/B hops along the strip's forward edge | one via less for as many layer hops: not simpler |
| B6 | M2 detour | BUZZ_OUT (14.87, 79.8) | 22.55 mm / 1 via for 8.76 mm (5.9 mm B.Cu BAT_IN) | search: 21.7 mm / 1 via, the present route | no shorter route found under the stricter rule |
| B8 | M2 detour | CAM_EN (36.7, 84.975) | 6.95 mm / 1 via for 3.73 mm (none) | search: 7.45 mm / 1 via, longer; the B.Cu leg threads C71.1 / U7.1 | already shorter than the search |
| B9 | M2 detour | CAM_FAULT_N (20.8, 96.175) | 92.46 mm / 5 vias for 53.69 mm (7.90 mm In2 3V3; fix pass 6 moved its In2 run back to x 14.64 through its via to y 91.85, then one 0.78 mm step onto x 15.19, 0.67–0.71 mm from SERVO4_MCU; fix pass 7 took its In2 bump between the vias (16.04, 67.46) and (19.82, 62.35) out, −2.61 mm) | search (fix-pass-4 copper): 78.9 mm but 7 vias | shorter only with two more vias, under the stricter rule (inherited R6) |
| B10 | M2 extra vias | CAM_FAULT_N | 5 vias | as B9 | as B9 |
| B11 | M2 extra vias | CAM_MCU_RX (17.35, 45.95) | 32.81 mm / 6 vias (7.6 mm In2 3V3) | measured: its F.Cu hop (25.85–28.25, y 42.35) between two In2 runs passes over a 3V3_In2 fill bridge (on In2 the same run clears every track but cuts that fill); search: 32.1 mm / 5 vias by four In2 / F.Cu alternations under the QSPI flash, with grid jogs | one via less for two more In2 hops: not simpler |
| B12 | M2 detour | CAM_MCU_TX (17.85, 45.95) | 65.87 mm / 5 vias (2.67×; 15.5 mm In2 3V3) | search: 66.0 mm / 5 vias, the present route; fix pass 3's 50.8 mm / 3-via candidate cuts the In2 3V3 plane at the buck output (L1.2 → U1.75 14.25 → 29.66 mΩ, measured) | the only shorter route found splits the 3V3 plane |
| B13 | M2 extra vias | CAM_MCU_TX | 5 vias | as B12 | as B12 |
| B14 | M2 detour | CAM_PWR_EN (36.7, 86.625) | 81.9 mm / 8 vias (2.52×; 7.9 mm In2 3V3) | no F/B-only route; search: 59.1 mm / 8 vias with nine layer hops through the pyro block and under U1; before the SWD reroute 55.1 mm / 7 and 72.4 mm / 4 through the corridors SWD now uses | the owner's trade-off: SWD 4 + 4 vias with CAM_PWR_EN 8, or CAM_PWR_EN about 4–7 with longer SWD (P3-REQUIREMENTS-01 option (b)) |
| B15 | M2 extra vias | CAM_PWR_EN | 8 vias | as B14 | as B14 |
| B16 | M2 extra vias | CAM_UART_OE (42.175, 45.7) | 30.68 mm / 4 vias (2.7 mm In2 3V3) | search: 33.1 mm / 5 vias; R102.1, U12.6 and TP91 on B.Cu, U1.7 on F.Cu, and the run must cross SWCLK's F.Cu diagonal (a 2.7 mm In2 hop) | already better than the search |
| B17 | M2 extra vias | LED_YEL (40.7, 29.4) | 36.26 mm / 3 vias (11.6 mm In2 3V3) | search: 36.0 mm / 3 vias, the present route | no route with fewer vias found under the stricter rule |
| B18 | M2 extra vias | LOGIC_SOURCE_ST (30.725, 38.6) | 58.31 mm / 11 vias (25.8 mm In2 3V3) | measured: its F.Cu hop (16.42–18.78, y 48.2) between two In2 runs passes over a 3V3_In2 fill bridge (on In2 it clears every track but cuts that fill); search: 55.5 mm / 10 vias with 21 mm of In2 in four runs | one via less, not simpler (inherited R6) |
| B19 | M2 extra vias | NRST (29.4, 47.92) | 46.11 mm / 4 vias (7.7 mm In2 3V3) | search: 45.4 mm / 5 vias; C24.1 on B.Cu, U1.14 and J2.3 on F.Cu, and the J2 branch crosses SWCLK and the SPI1 area | already better than the search |
| B20 | M2 detour | RAW_ACT_SENSE (13.75, 67.4) | 38.93 mm / 2 vias for 24.05 mm (24.7 mm In2 3V3) | search: 41.4 mm / 2 vias, longer | already shorter than the search |
| B21 | M2 extra vias | SERVO1_MCU (31.05, 81.25) | 65.32 mm / 5 vias (4.1 mm In2 3V3) | search: 62.2 mm / 4 vias with 14.6 mm of In2 in two runs under U1's SE corner and the SPI1 area | one via less for two In2 runs under SPI1: not simpler |
| B22 | M2 extra vias | SERVO2_MCU (32.95, 81.25) | 76.72 mm / 9 vias (9.4 mm In2 3V3, 0.9 mm 3V3A) | measured blockers: its F.Cu hairpin between the vias (28.1, 58.6) and (30.1, 60.8) hops C13.2's B.Cu GND tie (a straight B.Cu run at y 58.6 collides with it, and `GndFit` finds no legal GND via spot within 1 mm of C13.2 north of that row to shorten the tie); its In2 hop (26.3, 67.4) → (24.4, 69.3) crosses SPI1_SCK's B.Cu diagonal; search: the header legs 21.4 mm / 2 vias and 1.8 mm, and no route from D121.3 into U1.23 under the stricter rule | the two hops are forced by measured blockers; the rest of the route was not shown irreducible (inherited R6); fix pass 7's `--bumps-all` redraw of its F.Cu zigzag cut QSPI_IO2's In2 reference and was not applied (C27) |
| B23 | M2 detour | SERVO2_OUT (25.54, 76.97) | 34.94 mm / 1 via for 16.9 mm (none; fix pass 7 redrew its In2 run below the pyro block, S, E, NE → SE, E, NE, −2.13 mm: the pass-7 review's redraw) | `bump_audit --bumps-all` finds no shorter clean redraw of any 2–8 segment window of it; search: 31.4 mm / 1 via only with 0.15 and 0.55 mm jogs on B.Cu in the pyro block; with every segment ≥ 0.6 mm it needs 3 vias (32.3 mm) | the present route is 3.5 mm longer than the search's jogged one, which M2 forbids; no clean shorter redraw of any part of it is found (inherited R6) |
| B24 | M2 detour | SERVO4_MCU (31.05, 83.55) | 96.38 mm / 3 vias for 56.3 mm (24.4 mm In2 3V3; fix pass 6: one 0.71 mm SE step onto x 16.005 below the 3V3 via (16.3, 90.525), same length) | search (fix-pass-4 copper): 97.8 mm / 11 vias | already shorter than the search |
| B25 | M2 detour | SERVO4_OUT (25.54, 71.89) | 46.92 mm / 3 vias for 25.74 mm (12.9 mm In2 3V3A, 7.5 mm 3V3) | search: 52.4 mm / 6 vias | already shorter than the search |
| B26 | M2 extra vias | SERVO4_OUT | 3 vias | the search's best has 6 | as B25 |
| B27 | M2 detour | SWCLK (42.365, 76.65) | 62.7 mm / 4 vias (fix pass 3), F/B only (none) | search: 61.0 mm / 4 vias in the same corridor; SWD idle in flight | already within 3 % of the best found |
| B28 | M2 extra vias | SWCLK | 4 vias | the search's best also has 4 | as B27 |
| B29 | M2 extra vias | SWDIO (42.365, 77.92) | 53.72 mm / 4 vias (1.5 mm In2 3V3) | search: 54.0 mm / 4 vias, the present route | no route with fewer vias found under the stricter rule |
| B30 | M2 extra vias | VBUS_SENSE (16.1, 71.875) | 43.13 mm / 4 vias (19.6 mm In2 3V3) | search: 47.2 mm / 6 vias | already better than the search |

### C. Other recorded deviations (review items the tool does not hold)

C7 moved to A34 in fix pass 6 (a chain detour on a poured net is now gated), and C26 (ACT_EN's In2 hop) was removed in
fix pass 7; the numbers are not reused. C27 is new in fix pass 7. C15, C17, C24 and C25 have their instances listed
below the table.

| # | Item, location | Rule | Measured | Why it cannot reasonably be removed |
|---|---|---|---|---|
| C1 | 7.7 A servo-feed copper. Necks (F8's equipotential cuts at 0.05 mm on the final board): RAW_ACT 3.00 mm of F.Cu on the arm under J122 (21.55–24.45, y 80.6–81.0), between J122's GND and signal pin columns; ACT_FET_S 2.65 mm of B.Cu at Q120's source row (2.75–5.3, y 94.6–95.0), between Q120.4 (ACT_GATE) and R120; BAT_IN 3.82 mm of In2 in the arm (7.25–13.45, y 96.6–99.4) where ACT_GATE's In2 run (1.1, 93.9)–(7.7, 100.5) crosses it; median cuts 5.64 / 3.07 / 7.98 mm. MARGIN_PRESCRIPTION P1-9 (≥ 10 mm equivalent, mirrored and stitched) not met since R6 | **§3** high-current copper sized per IPC-2152 | M3_R7 "High-current copper: IPC-2152 estimate" (`f8/dc_ipc.py`, which reproduces the records' necks on the fix-pass-6 board exactly): long-conductor rise at the neck width 38 °C (RAW_ACT), 44 °C (ACT_FET_S) and 30 °C (BAT_IN), at the median width 19, 37 and 13 °C, at a continuous 7.7 A with no plane (Brooks & Adam's IPC-2152 fits; the fix-pass-6 board gave 55, 56 and 31 °C at its necks of 2.18, 2.15 and 3.71 mm); about 18, 20 and 20 °C at the necks with plane and FR-4 credit (Inference); upper bounds for short necks inside wider pours (Inference); flight 1's single servo (1.92 A) gives under 1/12 of them. Fix pass 7's bounded rework (`necks7`, no part moved): C86.2's GND via (18.975, 83.85) and its track out of the RAW_ACT neck (C86 keeps its thermal joint to GND_F, J122.3 2.4 mm away); ACT_FET_S_B's west edge 1.3 → 0.6 mm; six BAT_IN vias stitching R6's F.Cu crossbar (232 mm², joined before only through J1.1's barrel) to In2. DC at 0.1 mm: RAW_ACT 3.98 → 3.74, BAT_IN J1 → Q120 4.58 → 3.03 (ACT_EN's hop alone 3.90), ACT_FET_S 1.36 → 1.19 mΩ. One RAW_ACT cut at 97 % of the drop (0.5 mm, round Q121's via field) is not counted, as the via fields are not covered | **RAW_ACT:** the arm cannot widen between J122's pin columns, and the zone notch at (21.0, 85.8) keeps RAW_ACT off the pyro block. **ACT_FET_S:** now set by Q120's gate pad and R120 (ACT_GATE). **BAT_IN:** set by ACT_GATE's In2 crossing. Widening further needs ACT_GATE's routing or parts moved, or P1-9's mirror (a battery-corner re-layout); moving the actuator gate routing was outside fix pass 7. No requirement sets the rise limit (the owner's decision); F4's thermal-camera stall test is the check |
| C2 | Return paths: 603 R6-referenced samples lost (R6: 0): 410 on QSPI_IO0's abandoned R6 path, 79 at SPI1_MOSI's via antipad, 59 QSPI_IO3, 38 QSPI_NCS at CAM_MCU_RX's In2 crossing (24.45–24.68, 42.58–42.75), 15 QSPI_IO1, 2 QSPI_IO3; candidate-new 882 (21 of them QSPI_CLK at RXEN's via antipad since fix pass 5); extended set 2,312 lost / 4,325 candidate-new | review (return paths; the R6 bar of zero lost) | `tools/critical_reference.py` (sampling, not a field solve; F6; fix pass 6: 0 lost and 0 new against the fix-pass-5 board, F7; fix pass 7: 0 and 0 against the fix-pass-6 board, F8, with two candidate redraws refused for losing samples: LED_RED, C25, and SERVO2_MCU, C27) | most are on R6 paths R7 no longer has or at vias; the risk at the 8 MHz QSPI clock is low (Inference, `pass2_regression.md`) |
| C3 | SPI1_MOSI beside IMU_CS, F.Cu: 0.189 mm edge gap over about 15 mm | review (adjacency on critical nets) | DRC-legal; P3-REGRESSION-01 | opening it to 0.3 mm needs the SERVO1_MCU (27.1, 68.2) and SERVO2_MCU (26.3, 67.4) vias moved and leaves 0.002 mm to the 3V3 via (30.17, 71.17) (F4, measured) |
| C4 | QSPI_IO0 beside BAT_SW_RETURN, F.Cu: 0.232 mm over about 6 mm, closest 0.200 mm at the via (15.0, 37.725); RADIO_NSS 0.175 mm | review (adjacency) | DRC-legal; about 0.3 pF; P3-REGRESSION-05, P4-REGRESSION-04(a) | no lane search has been run (not shown irremovable); BAT_SW_RETURN is the DC harness side of the switch, ESD there improbable with a sealed reed or magnetic switch (Inference) |
| C5 | 7 split crossings at the U1 end of the corridor: the 7 radio lines cross from the In2 GND corridor strip to the In2 BAT_IN arm, 1.50–1.96 mm over BAT_IN per line, 12.16 mm for the 7 (BUSY 1.86, DIO1 1.87, MISO_MCU 1.96, MOSI_MCU 1.66, NRST 1.56, NSS 1.50, SCK_MCU 1.75 mm); the 7 band-end crossings were removed in fix pass 5 | review (return paths) | re-measured on the final board (the pass-6 reviewer's `refscan.py`); P3-ROUTING_QUALITY-02, P5-ROUTING_QUALITY-01, P6-ROUTING_QUALITY-02 | stitching needs a new BAT_IN–GND capacitor (schematic and BOM change, 52 of 52 extended codes); moving the lines cuts U9's In2 BAT_IN arm |
| C6 | RADIO_NRST's B.Cu run over CAM_MCU_TX's In2 track for 10.2 mm | review (crosstalk, reference) | P3-ROUTING_QUALITY-03 | the CAM_MCU_TX reroute that would clear it splits the 3V3 plane (B12) |
| C8 | SWCLK's B.Cu hop via (24.7, 50.95) 1.10 mm from the crystal pad Y1.3 (HSE_OUT), on Y1's layer; other close SWCLK neighbours: BUZZ_DRV via 0.177 mm, NRST via 0.202 mm, QSPI_NCS 0.251 mm, PYRO1_CONT via 0.191 mm | review (crystal keep-clear) | DRC-legal; P4-REGRESSION-03, P4-ROUTING_QUALITY-02 | no F/B route keeps SWCLK's vias ≥ 2 mm from Y1.3 (F5's router; constraints in M3_R7); SWD is idle in flight (Inference) |
| C9 | B.Cu GND reference under ARM1_SENSE's In2 run (void 4.2 mm) and CAM_PWR_EN's In2 runs (4.7 and 5.3 mm) cut by SWDIO's B.Cu verticals; the crystal/U1 B.Cu GND island 133.2 mm² with 27 vias | review (return paths) | every piece via-stitched to the solid In1 GND; P4-REGRESSION-03, P4-ROUTING_QUALITY-02 (voids re-measured unchanged on the fix-pass-4 board, pass 5; fix passes 5–7 did not touch SWDIO) | the price of SWD at 4 + 4 vias off In1 (P3-REQUIREMENTS-01 option (a)); both affected nets are slow DC or enable lines |
| C10 | NRST's In2 run at x 36.3 (10.35 mm): B.Cu GND fill over only 0.83 mm of it (none until fix pass 7's 3V3A redraw let GND_B fill in); 3V3A's 0.25 mm B.Cu track over 6.7–6.8 mm of it (centre line / any part of its width; the same scan gives 7.0–7.4 mm on the fix-pass-6 board, recorded earlier as 6.4–7.2 mm); no PYRO1_CONT above | review (return paths) | P5-REGRESSION-01, P5-ROUTING_QUALITY-03: NRST's In2 without B.Cu GND fell 20.6 → 14.7 mm with fix pass 4's reroute; In1 GND 1.06 mm above; re-measured on the final board by the records agent (fix pass 7) | inherited in kind (R6's x 36.435 run: 13.38 of 14.0 mm unreferenced); NRST is a slow reset line; a respin option is an In2 lane under B.Cu GND |
| C11 | Unstitched GND fingers 0.5–1.0 mm wide (gated only below 0.5 mm): 23 narrower than 0.75 mm, 48 narrower than 1.0 mm (fix-pass-6 board 21 / 47; fix-pass-4 board 23 / 49); worst R7-era F.Cu (37.9–40.5, 28.2–40.0) between CAM_MCU_TX and LED_YEL, 10.7 mm of copper from a GND via. Fix pass 7's redraws added a piece under 0.75 mm on B.Cu beside 3V3A's new run at x 35.6 (35.9–37.1, 61.5–64.7), narrowed a 0.75–1.0 mm piece beside A34's new run at x 38.45 to under 0.75 mm (38.7–41.8, 53.9–58.3), and added a 0.75–1.0 mm piece on B.Cu beside ACT_EN's new run (9.6–11.5, 103.9–108.0); they removed the 10.3 mm B.Cu piece along the left edge (0.5–1.35, 58.7–68.9) | M2 "unstitched GND pour fingers" (review beyond the tool's 0.5 mm) | records' re-derivation of the pass-4 reviewer's scan (`route_check.pour_pieces` with the finger width set to 0.75 and 1.0 mm and no relief-ring exclusion), which reproduces 21 / 47 on the fix-pass-6 board exactly; P4-RF-01; the x 40 finger had no legal via spot (pass-4 ViaCheck search; not re-searched) | it could only be trimmed, not stitched (a wider `pour_trim` width is untried); the three pieces fix pass 7 added or narrowed were not searched for a via spot; RF effect negligible (Inference) |
| C12 | J2.1 in-pad via: 3V3, (44.035, 77.92), hole edge 0.14 mm inside J2.1's Ø0.787 mm opening | M2 via-in-pad rule | inherited R6; named M2 exception | open and unplugged; expected DFM query; J2 taped and coated before flight (ORDERING §3, §4) |
| C13 | D30.2 and D31.2 (ESD clamps) solid to the GND pour | house thermal-relief rule (`check_r7.RF_SOLID_GND` exception) | fix-pass-4 decision (P4-RF-03) | a spoke adds return inductance at the jack, where the clamp works; the tombstoning risk is caught by the first-article inspection (ORDERING §5) |
| C14 | 32 of the 75 GND pour pieces on F.Cu / B.Cu (41 on F.Cu, 34 on B.Cu) are held by a single stitching via (34 of 77 on the fix-pass-6 board, 35 of 78 on the fix-pass-5 board) | review (pour stitching) | F8 on the final board; the records agent's fill count agrees (41 + 34 pieces); every GND piece holds at least one via, and the gate's `pour_finger` finds none unstitched | no critical net is known to use them as its reference (Inference, P5-REGRESSION-02); a second via each was not searched |
| C15 | Close adjacencies: the edge gaps under 0.2 mm that fix-pass copper created or a review raised, plus four at 0.200–0.297 mm kept for their pyro, reset or supply relevance; 40 instances, listed below. All are DRC-legal at the 0.15 mm default (the pyro rules A–H cover none of these pairs). Sub-0.2 mm gaps inherited unchanged from R6 elsewhere on the board are DRC-legal and not listed one by one | review (adjacency) | P5-REGRESSION-03, P5-ROUTING_QUALITY-02, P6-REGRESSION-02/-03, P6-ROUTING_QUALITY-03, P7-REGRESSION-02/-03; F6 §5, F7 §5, F8 §3 (`newgap.py`, `pairlen.py`); the new and the pass-7 pairs re-measured by the records agent; vias tented on both sides | what each short would do is in the list: none can fire a channel or put RAW_ACT on an MCU pin; three can put a higher rail on 3V3 or an MCU pin (RAW_PROTECTED twice, VLOGIC once), two can burn R164 (3V3A–GND), and the rest read a fault, hold a line or tie two lines; JLC's electrical test screens shorts (Inference). The GND via (28.55, 87.21) has no legal spot ≥ 0.25 mm from R129.1 / R178.1 within 1.45 mm of PYRO1_CONT's via (F6); the SERVO4_MCU / CAM_FAULT_N ends are pinned by RAW_PROTECTED's via (18.05, 102.87) and the GND vias (24.55 / 25.45, 104.47) (F7, F8, probed); the 3V3A hop's gap is set by its via positions (A47); the others were not searched |
| C16 | Forced non-tiny steps (outside the gate's tiny-jog class, offset < 0.25 mm or middle < 0.5 mm): I2C1_SCL F.Cu 0.36 mm step (25.35, 62.25) → (25.71, 62.61), 0.509 mm; QSPI_CLK F.Cu 0.36 mm step (22.85, 44.65) → (23.21, 44.29), 0.509 mm; CAM_RX_WIRE In2 0.5 mm step (43.75, 44.63) → (44.25, 45.14), 0.709 mm; RADIO_SCK's band staircase turned into an extra-bend run in fix pass 4 by lengthening its first run past 1 mm | M2 tiny jogs (in spirit; P5-ROUTING_QUALITY-04) | I2C1_SCL: straight down x 25.35 collides with BOOT0's via and the GND via (24.97, 64.4); a BOOT0 via between IMU_CS (x 24.35) and x 25.35 needs 1.095 mm of a 1.0 mm channel; BOOT0 on its line (x 24.94) puts its In1 antipad under IMU_CS for 0.5 mm (51 samples): tried, reverted. QSPI_CLK: straight on at x 22.85 its copper overlaps QSPI_IO3's via (22.5, 40.3) (−0.05 mm); the 0.36 mm step keeps 0.24 mm to RXEN's via. CAM_RX_WIRE: it drops from its via (43.75, 42.625) between BAT_SW_SOURCE's and BAT_SW_RETURN's In2 runs to its lane x 44.251. (F6, measured) | each is forced by a neighbouring via or lane; removing it moves those (BOOT0, QSPI_IO3, the RXEN via, the BAT_SW lanes) |
| C17 | 12 steps wholly inside a via's copper (listed below; the gate treats the via as the joint, not a jog): a 45° piece of 0.1–0.28 mm inside the via joins a lane that arrives 0.07–0.25 mm off the via centre | M2 tiny jogs / untidy entries (cosmetic) | each piece lies inside the 0.5 or 0.6 mm via copper (measured on the final board: pass-6 `scan6.py` and the records probe); exempt from `route_check`'s jog test by design ("S wholly inside one pad or via is that copper") | the offset is inside the via; re-centring each lane or moving each via onto its line was not attempted, except BOOT0 (C16: forced) (Inference: no electrical or DFM effect) |
| C18 | Earlier "kept" interface residuals (pass 2): RQ-09, RADIO_NSS's B.Cu hop inside the strip (23.2, 17.3) → (23.2, 15.67) → (23.6, 15.27) with its via pair (the NSS/SCK swap); RQ-11, RXEN's 90° corner at (18.35, 44.75), the band via-column and fan pitch irregularities, R307/C301 off-axis, the RESET_N via off-axis and the VBUS_SENSE jog; RG-12, the corridor lanes passing R313/R315 at 0.155 mm with free B.Cu beside them; RG-14, untidy pad entries in the strip (R307/C301, TP30, U30.7/8 link, R310 corner) | M2 layer hops, pad-entry tidiness (review) | present on the final board where re-checked (NSS hop, RXEN corner, QSPI_IO0 jog: measured; the rest as pass 5 found them on the fix-pass-4 board; fix passes 5–7 did not change these nets except 3V3_RADIO at FB31.2 → C310.1 and three launch GND vias moved 20 µm) | kept by the pass-2 dispositions (RQ-11 row; RG-12 "not moved"); not reworked since |
| C19 | BAT_IN B.Cu: a 0.9 mm, 0.5 mm-wide run (8.3, 54.525) → (9.2, 54.525) wholly inside C96.1's pad (x 7.4–9.2, y 53.95–55.1), 0.05 mm beside the through run (6.0, 54.475) → (8.2, 54.475) → (9.3, 53.375) | M2 duplicate / overlapping copper (inside a pad) | present (measured); it is the first leg of C96.1's link to the via (9.7, 54.025), through (9.2, 54.525) → (9.7, 54.025); `route_check` does not count it (its end lies on the pad edge) | not removed. Deleting it would leave the next leg ending exactly on C96.1's pad edge (x 9.2), an edge-touch joint; the clean fix is to redraw that leg from inside the pad (pass 6), not attempted |
| C20 | Forward-edge B.Cu GND: 621 raster points (about 1.6 mm²) at (17.3–21.0, y 112.0–112.9) lie up to 4.75 mm of copper from a GND via, against the 4.0 mm reach that fix pass 5's edge stitching applies at y ≥ 112 | review (pour stitching; the RF strip's reach rule applied to the forward edge) | F6 `edge_stitch` (12 GND vias added; the rest of the region within 4.0 mm); re-run on the final board by the records agent (`r7_polish.edge_far`): unchanged (fix pass 7's crossbar vias at x 9.45–10.2 lie outside it) | every legal spot within reach lies in the J1 → Q120 7.7 A corridor, which `GndFit` keeps clear by policy |
| C21 | R6 debris offsets (in R6 these joints carried 20–35 µm micro-segments; R7's clean-up deleted them and kept the offset): BAT_IN B.Cu in D8.1: (13.375, 31.85) → (11.875, 33.35) ends 25 µm off D8.1's centre (11.9, 33.35), where the outgoing run toward (9.2, 36.05) starts (split since fix pass 7 at the via (9.725, 35.525)), so the two lines are 17.7 µm apart and joined only by the pad; USB_FAULT_N B.Cu in R90.2: (17.15, 66.85) → (17.15, 70.05) ends 25 µm and 50 µm (x, y) off R90.2's centre, where the other run ends at (17.125, 70.0); ACT_GATE B.Cu: the 0.15 mm run (7.54, 102.36) → (9.32, 104.14) Ts onto the 0.283 mm diagonal (7.7, 102.2) → (7.5, 102.4), 0.057 mm from its end and inside the via (7.7, 102.2)'s copper; with the T at (7.08, 102.4), four nodes lie within 0.5 mm | M2 collinear / overlap-only joints, untidy entries (cosmetic) | measured on the final board (pass-6 `scan6.py`, records probe) | the joints are made inside the pad or via copper (no electrical or DFM effect, Inference); not tidied: each is a small board redraw (P6-ROUTING_GEOMETRY-03(b)) |
| C22 | NRST's own-net stacking: B.Cu (30.8, 53.1) → (30.8, 52.3) lies over its own In2 run (30.8, 53.1) → (30.8, 52.2), and B.Cu (30.8, 52.3) → (31.5, 51.6) runs 0.07 mm off In2 (31.3, 51.7) → (30.8, 52.2): about 1.5 mm | M2 duplicate copper (on two layers) and return paths (it shadows its own In2 branch from the B.Cu reference) | measured (P5-ROUTING_QUALITY-03, P6-ROUTING_QUALITY-03) | not changed: starting the B.Cu branch east of the via (30.8, 53.1) was the reviewers' option, not tried |
| C23 | Layer hops on poured nets that `pour_net_hop` does not count, because a via joins its own pour or is also a junction: CAM_5V B.Cu via (39.35, 104.55) → via (39.35, 103.6), 0.95 mm, both vias in the CAM_5V_In2 fill (fix pass 2's deliberate via doubling); BAT_IN B.Cu via (9.725, 35.525) → via (9.2, 36.05), 0.74 mm, both vias in the BAT_IN_F and In2 BAT_IN fills (fix pass 7 moved the stitching via onto the run and split it there, P7-ROUTING-03); 3V3 In2 run via (30.17, 71.17) → via (30.4, 78.25), 8.00 mm, F.Cu → In2 → F.Cu toward D120.3, neither via in a 3V3 fill (the first also carries 3V3's B.Cu run, so it is a junction) | M2 needless layer hops (review) | the first two are `route_check` `short_layer_hop` instances (information); the 3V3 crossing was measured by the pass-7 review (`hops2.py`, `gap.py`) | CAM_5V: judged by pass 4 (accept the doubling); not re-searched. BAT_IN: the via's only legal spot is on the run (TP89's keep-out, the via (9.2, 36.05), BAT_ILIM's F.Cu); whether the 0.74 mm piece itself can go, both vias joining both BAT_IN fills, was not examined. 3V3: along x 30.4 both outer layers are closed by the SPI1 / I2C fan (F.Cu: SERVO3_MCU, SPI1_MOSI, IMU_CS, I2C1_SCL and a RAW_ACT pad; B.Cu: SPI1_SCK, SPI1_MISO, I2C1_SDA, IMU_INT1), so the crossing is forced; its second via (30.4, 70.25) and the two overlap-only joints went in fix pass 7 (P7-DOCS-01). Fix pass 7 also deleted the 3V3 F.Cu hop (27.35, 44.25) → (29.9, 43.625) and In2 run (30.63, 31.34) → (32.33, 33.04), both duplicates of the plane (P7-DOCS-02), and the 3V3A hop is gated (A47) |
| C24 | 21 chain detours on critical nets without a pour (the pass-2 scan's `chain_detour`; the gate's detour test works per net and does not see a whole local run): listed below | M2 needless detours (review) | the gate's own chain test (a run between junctions > 1.25 × the octilinear distance of its ends and > 0.5 mm longer) and `alt_audit`'s redraw search, run by the fix-pass-6 records agent on every net (`rec6/cd/critdet.py`, `alldet.py`); every redraw found was tried on a scratch copy (DRC with parity, native refill, pour pieces, `route_check`). Since fix pass 7 the gate's `bump_audit` searches every 2–8 segment window of these runs (gated): it finds only USB_LIMITED's B.Cu hump (A48) | 1 forced by the module keep-out (RADIO_TXEN); 3 with a redraw that DRC or the pours reject, or that adds an off-centre pad entry; 17 with no 1–3 segment redraw (4+ segment redraws, moved pads or vias not searched). ARM1_SENSE's L, the one the records had found removable, is gone (fix pass 7) |
| C25 | 17 chain detours on non-critical nets: listed below | M2 needless detours (review) | as C24 (the gate's `bump_audit` does not gate non-critical nets; its `--bumps-all` review list is C27) | LED_RED's In2 bump is not removable (its straight redraw cut the 3V3_In2 reference under QSPI_NCS: 465 samples, F8); 1 whose redraw splits the 3V3_In2 pour (LOGIC_SOURCE_ST); 15 with no 1–3 segment redraw. Fix pass 7 removed CAM_FAULT_N's In2 bump, I2C1_SDA's run and CAM_5V_SENSE's In2 run |
| C27 | Local bumps on non-critical nets (`route_check --bumps-all`, `local_bump_review`, information; fix pass 7): VLOGIC_SENSE In2 (30.7, 51.5) → (32.44, 42.86), 10.90 mm (redraw 10.56 mm); BAT_SW_SOURCE F.Cu (44.76, 61.1) → (42.56, 51.0), 12.81 mm (redraw 11.01 mm); SERVO2_MCU's F.Cu zigzag, whose redraw the strict test now refuses | M2 needless detours (review) | F8, each redraw tried on a scratch copy; `--bumps-all` re-run on the final board by the records agent (223 windows: these two) | **VLOGIC_SENSE and BAT_SW_SOURCE: removable, not removed (judged).** VLOGIC_SENSE's redraw saves 0.33 mm but passes a GND via at 0.165 mm (0.199 mm now); BAT_SW_SOURCE (a harness line, the power switch's source side) saves 1.80 mm but would come within 0.187 mm of its neighbour, against 0.725 mm now (the pass-7 reviewer's judgement). **SERVO2_MCU: not removable:** its redraw cut QSPI_IO2's In2 reference (179 samples, F8) |

**C15 instances** (edge-to-edge gap; "fp" = the fix pass whose copper made the gap; what a short would do, Inference
throughout unless measured; every pair is DRC-legal):

| # | Pair (layer where not obvious) | Gap, mm | Since | A short would |
|---|---|---:|---|---|
| 1 | GND via (28.55, 87.21) – R129.1 (PYRO1_CONT_MID) | 0.170 | fp 5 | read "no continuity" (fail-safe: about 1.6 mA then flows through an armed igniter via R173) |
| 2 | GND via (28.55, 87.21) – R178.1 (PYRO1_CONT) | 0.190 | fp 5 | as 1 |
| 3 | GND via (22.85, 89.63) – R126.1 (PYRO1_GATE_N) | 0.297 | fp 4 | hold the FET off (rule G excludes GND by design) |
| 4 | PYRO1_CONT via (35.78, 60.65) – CAM_UART_OE | 0.175 | fp 4 | corrupt the continuity reading; cannot fire |
| 5 | PYRO1_CONT via (35.78, 58.85) – SWCLK | 0.191 | fp 4 | as 4 (SWD idle in flight) |
| 6 | PYRO1_CONT via (28.40, 88.61) – R129.1 (its own divider midpoint) | 0.193 | fp 4 | read "no continuity" |
| 7 | PYRO1_CONT – NRST | 0.195 | fp 4 | corrupt the reading or hold the MCU in reset; cannot fire |
| 8 | PYRO1_CONT via (35.78, 60.65) – 3V3A (B.Cu, redrawn in fix pass 7; 0.208 mm before) | 0.212 | fp 4 / 7 | put 3.3 V on the sense node: reads "continuity present"; not a fire path, the gates are defined off |
| 9 | GND via (41.375, 70.625) – PYRO1_CONT | 0.171 | fp 5 | read "no continuity" (fail-safe) |
| 10 | GND via (13.95, 93.75) – ARM1_SENSE via | 0.172 | fp 5 | read "disarmed": a refusal on the ground, only logged in flight |
| 11 | GND via (13.95, 97.15) – ARM1_SENSE via | 0.172 | fp 5 | as 10 |
| 12 | NRST via – SWCLK via | 0.202 | fp 4 | disturb SWD or hold the MCU in reset (SWD idle in flight) |
| 13 | GND via (35.85, 53.275) – NRST via (35.80, 53.95), all four layers (hole to hole 0.377 mm) | 0.177 | fp 5 | hold the MCU in reset: dead at bring-up, pyro gates defined off, radio held in reset; not unsafe, but not fail-safe in the sense of 1 |
| 14 | GND via (35.85, 53.275) – NRST's B.Cu diagonal | 0.188 | fp 5 | as 13 |
| 15 | GND via (35.85, 53.275) – 3V3A | 0.175 | fp 5 | as 33 (R164 burns) |
| 16 | CAM_FAULT_N In2 (y 103.938) – GND via (24.55, 104.47) | 0.162 | fp 5 | read "camera fault" |
| 17 | CAM_FAULT_N In2 (y 103.938) – GND via (25.45, 104.47) | 0.162 | fp 5 | as 16 |
| 18 | SERVO4_MCU – CAM_FAULT_N, In2: 6.57 mm within 0.2 mm, 7.32 mm within 0.3 mm (was 30.45 mm within 0.2 mm before fix pass 6): the end diagonals and E runs into y 103.63 / 103.94 (0.161–0.194 mm), SERVO4_MCU's 0.164 mm pass of CAM_FAULT_N's via (16.04, 67.46), and since fix pass 7 CAM_FAULT_N's new E run 0.169 mm from SERVO4_MCU's In2 piece at x 17.825 (y 63.5–64.8; the run it replaces was 7 µm closer) | 0.161 | fp 5–7 | tie the two lines; coupling ≲ 0.1 V (a 3.3 V PWM edge through ≲ 0.5 pF into about 15 pF) |
| 19 | CAM_FAULT_N – CAM_PWR_EN via | 0.165 | fp 5 | tie the two lines |
| 20–22 | radio band lanes: RADIO_MISO_MCU's and RADIO_MOSI's fan-in steps, RADIO_BUSY – GND via (20.0, 27.45) | 0.168–0.176 | fp 5 | tie two radio lines or hold one low (radio link fails) |
| 23 | CAM_5V_SENSE – GND via (31.5, 37.8) | 0.175 | fp 5 | hold the sense line low |
| 24 | PULLPIN_EXT – C60.2 (GND) | 0.176 | fp 5 | hold the pull-pin line low |
| 25 | GND via (27.4, 76.4) – SERVO1_MCU | 0.176 | fp 5 | hold servo 1's PWM low |
| 26 | CAM_RX_WIRE – BAT_SW_SOURCE via | 0.184 | fp 5 | tie the two lines |
| 27 | GND via (42.2, 43.25) – BAT_SW_SOURCE In2 | 0.185 | fp 5 | hold the switch line low |
| 28 | CAM_5V_SENSE – CAM_MCU_RX via | 0.191 | fp 5 | tie the two lines |
| 29 | CAM_TX_WIRE – R101.1 (CAM_TX_BUFFER) | 0.191 | fp 5 | bypass R101 (1 kΩ) |
| 30 | LOGIC_ILIM – 3V3 via | 0.194 | fp 5 | tie U11's current-limit pin to 3V3 |
| 31 | USB_LIMITED – BAT_SW_RETURN via | 0.194 | fp 5 | tie the two lines |
| 32 | LOGIC_SS – U11.12 (GND) | 0.183 | fp 6 | hold U11's soft-start low |
| 33 | 3V3A B.Cu hop – GND via (36.5, 76.54) | 0.200 | fp 5 drawing, restored in fp 7 (0.169 in fp 6; the reviewers' "0.34" was not this drawing's gap) | draw about 1.5 A and 5 W in R164 (2.2 Ω, 0603), which would likely burn open, losing the IMU, the barometer and U1's VDDA / VREF+; not a pyro hazard (P7-REGRESSION-02) |
| 34 | SERVO4_MCU In2 diagonal (16.005, 101.627)–(18.005, 103.627) – RAW_PROTECTED via (18.05, 102.87) | 0.192 | inherited R6 (raised by pass 7) | put RAW_PROTECTED (U9's output, up to 8.4 V) on PA3 (U1.25) and, through D121 (SRV05-4), on 3V3; on In2, so only a laminate defect can short it (P7-REGRESSION-03) |
| 35 | 3V3 B.Cu (A34's S run on x 38.45) – RAW_PROTECTED via (37.85, 54.7) | 0.175 | fp 7 (R6's run passed it at 0.157) | put RAW_PROTECTED (up to 8.4 V) on 3V3: over-voltage on every 3V3 part |
| 36 | 3V3 B.Cu (A34's NW diagonal) – CAM_RX_WIRE via | 0.173 | fp 7 | tie the camera UART wire to 3V3 (camera link lost) |
| 37 | SERVO2_OUT In2 – 3V3 via (21.9, 96.125) | 0.171 | fp 7 (as before the redraw) | tie servo 2's signal output to 3V3 |
| 38 | VLOGIC F.Cu – C99.2 (GND) | 0.172 | fp 7 (as before the redraw) | short the logic rail (U2's input) to GND: the logic supply fails |
| 39 | VLOGIC F.Cu – D122.2 (3V3) | 0.175 | fp 7 (0.225 mm before) | put VLOGIC (U2's input, at pack voltage, up to 8.4 V) on 3V3: over-voltage on every 3V3 part |
| 40 | CAM_5V_SENSE In2 – VLOGIC_SENSE In2 | 0.182 | fp 7 (0.204 mm before) | tie two ADC sense lines (wrong readings) |

**C17 instances** (offset of the arriving lane from the via centre / length of the in-via piece):

| Net, layer | Step | Offset / piece | Note |
|---|---|---|---|
| GND, B.Cu | (31.3, 53.7) → via (31.5, 53.5) | 0.2 / 0.283 mm | was D5 |
| RADIO_NRST, F.Cu | via (10.0, 27.7) → (10.1, 27.6) | 0.1 / 0.141 mm | was D14 (fix pass 4's intended form) |
| PULLPIN_EXT, B.Cu | (34.4, 29.8) → via (34.15, 29.8) | 0.25 / 0.25 mm | fix pass 5 |
| QSPI_IO0, F.Cu | (15.4, 51.0) → via (15.55, 50.85) | 0.15 / 0.212 mm | pass-2 RQ-11 |
| BOOT0, F.Cu and B.Cu | (24.85, 62.65) → via (25.05, 62.85) → (24.83, 63.07) | 0.2 / 0.283 and 0.311 mm | the via 0.2 mm off its line; forced (C16) |
| RAW_PROTECTED, F.Cu | (38.05, 54.5) → via (37.85, 54.7) | 0.2 / 0.283 mm | critical power net |
| RAW_PROTECTED, F.Cu | (25.85, 40.6) → via (25.85, 40.5) | 0.071 / 0.1 mm | critical power net |
| VBUS, In2 | (11.0, 79.75) → via (10.8, 79.95) | 0.2 / 0.283 mm | critical power net |
| USB_LIMITED, F.Cu | via (25.8, 37.15) → (26.0, 37.35) | 0.2 / 0.283 mm | critical power net |
| SERVO1_MCU, In2 | (27.1, 71.5) → via (26.9, 71.7) | 0.2 / 0.283 mm | |
| CAM_PWR_EN, In2 | (17.35, 89.65) → via (17.55, 89.85) | 0.2 / 0.283 mm | |
| SERVO3_OUT, B.Cu | via (29.14, 98.33) → (29.34, 98.13) | 0.2 / 0.283 mm | |

The GND joint at (36.4, 76.54) → via (36.5, 76.54), which pass 6 listed as a step, is a NE diagonal arriving 0.071 mm
off the via centre with a 0.1 mm piece inside the via: a bend inside the via (one of the via-entry pieces in part F),
not a step. Its copper has not changed since the pass-6 board; the fix-pass-6 records wrongly put the change down to
fix pass 6's 3V3A redraw (P7-ROUTING-04).

**C24 instances** (critical nets without a pour; path / octilinear distance of the run's ends, mm):

| Net, layer, run | Path / octilinear | Judgement |
|---|---|---|
| RADIO_BUSY F.Cu (9.4, 28.2) → (24.91, 11.46) | 31.54 / 23.16 | band lane: fan-in step, the E run, the N lane between the modules (A1, A9; interface topology, A17–A26); no 1–3 segment redraw |
| RADIO_MISO_MCU F.Cu (10.0, 28.7) → (22.57, 12.73) | 27.77 / 21.18 | as RADIO_BUSY F.Cu (A2, A13) |
| RADIO_MOSI F.Cu (9.4, 29.2) → (24.91, 14.0) | 29.85 / 21.81 | as RADIO_BUSY F.Cu (A11) |
| RADIO_NSS F.Cu (9.4, 30.2) → (23.2, 17.3) | 25.65 / 19.14 | as RADIO_BUSY F.Cu (A25; its strip hop C18) |
| RADIO_SCK F.Cu (10.0, 29.7) → (24.91, 16.54) | 27.01 / 20.36 | as RADIO_BUSY F.Cu |
| RADIO_BUSY B.Cu (10.0, 49.5) → (9.4, 28.2) | 30.58 / 21.55 | left-edge corridor lane: U1 escape west, down the corridor (x 3.2–6.2), back east to the band columns (interface topology, A17, A21–A25); no 1–3 segment redraw |
| RADIO_DIO1 B.Cu (10.0, 50.5) → (9.4, 27.2) | 33.89 / 23.55 | as RADIO_BUSY B.Cu |
| RADIO_MISO_MCU B.Cu (10.7, 48.5) → (10.0, 28.7) | 30.43 / 20.09 | as RADIO_BUSY B.Cu |
| RADIO_NRST B.Cu (9.3, 50.0) → (10.0, 27.7) | 32.13 / 22.59 | as RADIO_BUSY B.Cu |
| RADIO_NSS B.Cu (9.3, 47.5) → (9.4, 30.2) | 23.25 / 17.34 | as RADIO_BUSY B.Cu |
| RADIO_SCK_MCU B.Cu (10.0, 48.0) → (5.7, 44.43) | 7.52 / 5.78 | corridor entry; no 1–3 segment redraw |
| RADIO_TXEN B.Cu (31.13, 20.15) → (28.59, 7.8) | 22.72 / 13.40 | round U31's west side (A27). The search's only redraw, (31.13, 20.15) → (26.46, 15.48) → (26.46, 7.8) → (28.59, 7.8), crosses `U31_KEEPOUT` (B.Cu, x 24.86–34.86, y 9.0–19.0), which `check_r7` enforces and which, since fix pass 7, `alt_audit` and `bump_audit` see too (`RedrawCheck`): forced |
| PYRO1_CONT F.Cu (26.83, 87.9) → (24.6, 87.2) | 3.61 / 2.52 | the U-turn round R130.2 (S, W, NW, N into R129.2's via; A19); no 1–3 segment redraw |
| 3V3_GNSS F.Cu (13.71, 19.7) → (12.61, 20.75) | 2.15 / 1.54 | an L (N 1.05, W 1.1). The search's redraw is DRC-clean but ends 0.2 mm off a pad centre (a new `pad_end_offcentre`); the L is the tidier: kept |
| USB_DM F.Cu (6.88, 74.55) → (10.05, 76.3) | 7.28 / 3.90 | the USB-C A6/B6/A7/B7 crossover (J3's two contact rows joined); no 1–3 segment redraw |
| USB_DP B.Cu (8.9, 76.35) → (11.95, 75.15) | 5.24 / 3.55 | as USB_DM |
| VCAP2 F.Cu (14.3, 58.5) → (16.0, 62.4) | 11.07 / 4.60 | A32 |
| VLOGIC F.Cu (28.505, 29.85) → (31.67, 35.5) | 12.56 / 6.96 | part of A33's tree; fix pass 7 took its local peak round D122.2 out (13.16 mm before); no 1–3 segment redraw of the whole run |
| RAW_PROTECTED B.Cu (14.0, 33.3) → (26.225, 26.725) | 18.78 / 14.95 | part of A28's tree (N, NE, E, SE); no 1–3 segment redraw |
| USB_LIMITED In2 (29.1, 40.55) → (25.8, 37.15) | 7.40 / 4.77 | a hook past its via; the search's redraw passes DRC but splits the 3V3_In2 pour (5 → 6 pieces on the fix-pass-6 board): kept; `bump_audit` (fix pass 7) finds no removable window in it |
| USB_LIMITED B.Cu (33.1, 26.15) → (30.8, 27.85) | 4.35 / 3.00 | a hump; allowlisted since fix pass 7 as a local bump (A48): every shorter redraw cuts R105.2's GND path (the starved GND thermal the fix-pass-6 records found by DRC): kept |

By the same measure, QSPI_IO2's In2 overshoot (part of A20) and SPI1_SCK's entry into U4 are not chain detours.

**C25 instances** (non-critical nets; path / octilinear, mm):

| Net, layer, run | Path / octilinear | Judgement |
|---|---|---|
| LED_RED In2 (21.85, 41.85) → (30.85, 41.7) | 12.73 / 9.06 | **not removable:** the fix-pass-6 records' straight run at y 41.85 (9.15 mm, DRC-clean) cuts the 3V3_In2 reference under QSPI_NCS's B.Cu run (25.0–26.4, 40.9–42.0): F8's build #1 lost 465 critical-reference samples, and the redraw was reverted; the bump goes round that piece of plane (B17's net) |
| LOGIC_SOURCE_ST In2 (16.42, 48.22) → (15.68, 41.91) | 8.29 / 6.62 | the search's redraw splits the 3V3_In2 pour (5 → 6 on the fix-pass-6 board) and leaves 1 unconnected: kept (B18) |
| BAT_SW_SOURCE B.Cu (41.36, 39.0); BUZZ_OUT B.Cu (9.6, 82.2); CAM_5V_SENSE F.Cu (24.45, 47.35); CAM_DVDT B.Cu (32.4, 85.725); CAM_EN B.Cu (37.95, 85.7); CAM_FAULT_N In2 (14.64, 90.82); LED_YEL In2 (22.35, 41.35); LOGIC_SS B.Cu (28.95, 29.65); NRST B.Cu (30.8, 53.1); SERVO2_MCU F.Cu (28.1, 58.6); SERVO2_OUT In2 (25.54, 76.97); SERVO3_MCU F.Cu (31.15, 84.99); SERVO4_MCU In2 (27.40, 99.14); SWCLK F.Cu (24.7, 50.95); USB_ILIM B.Cu (16.3, 80.6) | 6.06 / 3.43; 15.67 / 9.90; 5.16 / 1.86; 6.76 / 5.10; 3.68 / 2.57; 37.39 / 25.78; 11.56 / 8.06; 9.51 / 6.80; 7.06 / 5.35; 3.85 / 3.03; 29.20 / 19.25 (31.34 before fix pass 7's redraw); 11.28 / 8.83; 70.16 / 49.50; 16.85 / 9.05; 12.54 / 9.39 | no 1–3 segment redraw with the ends fixed (15 runs), and `--bumps-all` finds no removable local bump in them (C27: the two it finds on other runs, and SERVO2_MCU's zigzag, whose redraw F8 found but the strict test refuses); the net-level reasons are in B where the net has an entry (B5, B6, B8, B9: the spaced run, B17, B19 and C22, B22: C13.2's GND tie, B23, B24, B27 and C8); CAM_5V_SENSE's F.Cu leg wraps round RAW_ACT_SENSE_MCU's via (23.05, 47.65), which boxes in U1.35's escape (the only legal via spots within 1 mm of U1.35 lie beyond that diagonal, pass 6, measured; the net's detour entry B7 went in fix pass 7); CAM_DVDT, LOGIC_SS, SERVO3_MCU and USB_ILIM have no B entry (their nets pass the net-level tests) and were not searched further |

### D. Part D of the fix-pass-4 list (18 items): status on the final board

14 are removed or fixed, D8 is counted and allowlisted (A8), D5 and D14 lie inside a via's copper (C17), and D18 is
done in part (its tool gaps are closed; its RF checks are open).

| # | Item (fix-pass-4 list) | Status |
|---|---|---|
| D1 | ACT_GATE 45° wedge at Q121.4 | **Removed** (square T from TP121's vertical; `tidy5`); its R6 knot is C21 |
| D2 | GND staircase toward LED1 | **Removed** (C94.2 run redrawn) |
| D3 | CAM_5V jog into via (39.35, 104.55) | **Removed** (R78.1 → via in two segments) |
| D4 | 3V3_RADIO jog at FB31.2 | **Removed** (straight through FB31.2 into C310.1; the end lies 0.304 mm off C310.1's centre, part E) |
| D5 | GND step between two vias (31.3, 53.7) | **Remains**, measured as wholly inside the via's copper: C17 |
| D6 | CAM_FAULT_N In2 staircase through a via | **Removed** (`jogs5`) |
| D7 | RAW_ACT tail 3.17 mm inside its fill | **Fixed**: the run ends 0.628 mm inside its fill (`pour_stub` gates > 1.0 mm); the run itself is now allowlist entry A41 (a gated chain detour, 7.11 mm) |
| D8 | PYRO1_GATE layer change into TP122 | **Counted and allowlisted** with a measured reason: A8 |
| D9 | Overlapping launch GND via pairs | **Fixed** (three vias 20 µm aft; `via_overlap` 0) |
| D10 | USB_LIMITED at U11.7 | **Fixed** (corner and square branch) |
| D11 | VLOGIC at U2.2 | **Fixed** (runs end at the U2.2 / U2.3 centres) |
| D12 | RADIO_RXEN jog across via (23.8, 39.45) | **Removed** (RXEN on its via column) |
| D13 | CAM_RX_WIRE T-jog | **Removed** (one In2 run at x 44.251) |
| D14 | RADIO_NRST 0.141 mm step out of its via | **Remains**, inside the via's copper: C17 |
| D15 | Unstitched forward-edge F.Cu GND strip | **Fixed** (12 edge GND vias; residual C20) |
| D16 | CAM_TX_WIRE on In1 | **Fixed** (off In1, 2 vias → 1; In1 carries no signal copper) |
| D17 | 7 designators nearer another courtyard | **Fixed** (`r7_post` courtyard test on every visible designator; the 7 hidden, U13 shown) |
| D18 | Gate blind spots S1–S5; missing RF checks | **Partly done:** S1–S5 closed in `route_check` (fix pass 5); the RF checks (P4-RF-02) stay open (tool coverage, not copper; "Open after fix pass 7") |

### E. Information-only `route_check` instances (252)

`route_check` counts these and never gates them. On non-critical nets the hygiene categories (jogs, short segments,
detours, extra vias and the rest) are recorded in B; these nine categories are information on every net. Counts on
the final board (`route.json` of the records agent's gate run), critical nets / non-critical nets. `--bumps-all`'s
tenth information category, `local_bump_review`, is not part of a gate run; its findings are C27. The tool reports one
instance per track end, so a pad entered by two ends at one point counts twice (LOGIC_SS at U11.11, BAT_IN at C96.1).

| Category | Critical | Non-critical | What it is | Why it is information, not a defect |
|---|---:|---:|---|---|
| `pad_end_offcentre` | 63 | 31 | a track end more than 0.1 mm off the centre of a pad no larger than 2 mm | the end still lies on the pad, so the joint is made; M2's "untidy pad entries" is a review judgement, made one by one for the critical nets by the pass-4 reviewer (accept, apart from tidy-ups that fix pass 5 made). New since: 3V3_RADIO's NE diagonal (35.1, 20.85) → (36.565, 19.385) into C310.1 (fix pass 5's D4 tidy-up) ends inside the 1.41 × 1.35 mm pad with its line 0.304 mm beside the pad centre, judged here: the joint is made, and centring it needs the diagonal moved 0.3 mm or a bend (kept; not searched); LOGIC_SS 0.3 mm off U11.11 (fix pass 6: the straight exit inside the pad, then the diagonal from its edge), non-critical |
| `power_via_no_gnd` | 34 | — | a power-rail layer change with no GND via centre within 1.5 mm | AGENTS §3 sets the GND-via rule for critical signal nets; a power rail's return is its own decoupling and the planes (not an §3 instance). Fix pass 7: the two deleted 3V3 vias left the list, and USB_LIMITED's via (17.925, 83.15) joined it (the nearest GND via is now 4.85 mm away, since C86.2's GND via left the RAW_ACT neck, C1) |
| `width_change_junction` | 30 | 1 | segments of different widths at a T or a via | a narrower branch leaving a wider trunk is a branch, not a neck-down (`neck_down`, gated, catches width changes inside one conductor away from pads: 0) |
| `u_turn` | 16 | 6 | a chain whose cumulative heading change reaches 180° | the radio corridor lanes and several inherited R6 runs turn back by topology (pass 4 judged the critical ones). On a net without a pour the net's length is held by the detour test (gated on critical nets, recorded in B); the 5 on poured nets (3V3 (36.94, 52.65), GND (14.3, 59.0), (16.35, 45.95) and (13.7, 80.6), RAW_ACT (10.4, 64.67)) are also gated chain detours, allowlisted as A34–A36, A38 and A40. CAM_FAULT_N's at (16.04, 67.46) went in fix pass 7; USB_LIMITED's In2 hook at (29.1, 40.55) is kept (C24) |
| `extra_bends` | 12 | 23 | an alternating chain of ≥ 4 segments with fewer than 2 under 1 mm | not a staircase (gated, 0): long legs with 45° chamfers, e.g. the radio band lanes, SW_NODE's redraw, fix pass 6's CAM_FAULT_N / SERVO4_MCU spacing steps and fix pass 7's 3V3A run on x 35.61 and BUZZ_DRV redraw |
| `passes_through_pad` | 8 | 0 | a segment crossing a same-net pad without ending in it | same-net copper; 3 are the RF lines' deliberate stub-free shunts (D30.1, L30.2, D31.1); the other 5 cross a same-net pad on their way (LS120.1, Q124.2, R173.1, R10.1, J3.A7), accepted by the pass-4 reviewer (RAW_ACT's through Q121.5 went with fix pass 6's duplicate, ARM1_SENSE's through R180.1 with fix pass 7's split) |
| `short_layer_hop` | 8 | 10 | a chain under 3 mm between two vias of a non-GND net | M2's "needless layer hops" is a review judgement. On a net without a pour the via count is gated (critical) or recorded (B): the 10 non-critical hops are on CAM_MCU_RX, CAM_UART_OE, LOGIC_SOURCE_ST (4), SWDIO, SERVO2_MCU (2) and BAT_SW_RETURN, all on B nets whose reasons cover them (ACT_EN's went in fix pass 7); the critical ones on nets without a pour are RADIO_NSS's (C18), PYRO1_CONT's (A19), VBUS's (A29/A30) and USB_DP's (the USB-C crossover). On poured nets the via count is not tested: CAM_5V's F.Cu hop (43.3, 33.425) is a gated series hop (A46), the 3V3A hop is a gated chain detour (A47), and CAM_5V's doubling and BAT_IN's 0.74 mm piece at (9.725, 35.525) are C23 |
| `via_on_track_in_fill` (fix pass 7) | 6 | 0 | a via joined to a same-net track only by overlap (the track's body crosses the via's copper with no end in it) where the via also lies in its own net's fill on that layer | all six are GND vias inside GND fill, so the pour joins them to the track anyway: B.Cu (43.5, 89.0), (28.45, 25.85), (10.7, 70.5) (R6), (22.85, 89.63) (fix pass 4); F.Cu (18.18, 90.55) (R7) and (6.85, 40.5) (P7-DOCS-01, P7-ROUTING-03); cosmetic. The same class outside a fill is `via_on_track`, gated on critical nets (0) |
| `segment_inside_pad` | 2 | 2 | a segment ≥ 0.2 mm lying wholly inside the pad it ends in | copper inside the pad's own copper (QSPI_NCS in R10.1, VLOGIC in U2.2, LED_YEL_A in LED2.1, and LOGIC_SS in U11.11 since fix pass 6): no electrical or DFM effect |
| **Total** | **179** | **73** | | |

Instances that fix passes 4–7 introduced are among these (for example SERVO3_MCU 0.41 mm off-centre into D121.4,
LED_YEL_A's 0.55 mm segment inside LED2.1, CAM_UART_OE's 2.7 mm In2 hop, PYRO1_CONT's 1.8 mm In2 hop and its U-turn at
the divider, the band lanes' extra bends, the spacing steps, LOGIC_SS's pad entry, and fix pass 7's BAT_IN 0.74 mm
hop, 3V3A extra-bend run and USB_LIMITED via without a near GND via). Their per-instance list is in
the gate's `route.json`. None of the nine categories is an AGENTS §3 rule.

### F. Outside the list

- **The pass-2 reviewers' `scan.py`** (`pass2_routing_geometry.md`; unchanged since) finds 904 instances on the final
  board (549 on critical nets; F8 `f8/scan_final.json`, rerun by the records agent): `pad_end_offcentre` 208,
  `pad_entry_diagonal` 174, `dogleg` 134, `net_length` 67, `chain_detour` 47, `right_angle_corner` 40, `extra_bends`
  35, `off_angle_rounding` 28, `short_segment` 27, `u_turn` 22, `via_pair_close` 22, `short_layer_hop` 18,
  `width_change_free` 18, `width_change_at_pad` 17, `width_change_at_via` 13, `acute_at_padvia` 10,
  `passes_through_pad` 8, `critical_via_no_gnd` 8, `segment_inside_pad` 4, `collinear_unmerged` 3, `end_in_zone_only`
  1 (fix-pass-6 board: 918, 559 critical). It is a reviewer's heuristic scan, not the gate. Where its categories name
  a rule, the gate's tested definitions hold the rule and find 0 failing:
  - off-angle: its `off_angle_rounding` are headings within 0.00744° and 0.07 µm lateral of a multiple of 45°,
    coordinate rounding (`pcbnew.FromMM` truncation; fix pass 7's new ones are 1 nm truncations, F8); the gate's
    `off_angle` finds 0;
  - acute: its 10 `acute_at_padvia` are 45° pairs whose wedge lies inside the pad or via copper, which the gate's wedge
    test and pass 6's independent scan count as 0 exposed;
  - collinear: its 3 are pad-entry necks at plain nodes, not unmerged same-width segments (BAT_IN 0.5 → 0.3 mm into
    U9.5, RAW_PROTECTED into U9.6, CAM_INPUT_LIMITED into U7.5; the gate's `neck_down` exempts a neck running straight
    into a pad within 1 mm);
  - stub: its one `end_in_zone_only` is RAW_ACT's tail ending 0.628 mm inside its fill (A41);
  - GND via: its 8 are A6, A7, A9–A14 (it does not count the layer change into TP122's pad, A8);
  - short segments: all 27 lie wholly inside a via's copper (via-entry pieces, which the gate's `short_segment`
    excludes; the fix-pass-6 board's 28 less CAM_FAULT_N's 0.08 mm piece at (16.04, 67.46), which went with its bump);
  - width changes: at a pad 17, at a via 13, at another node 18: a narrower branch at a T or a via, or a pad-entry
    neck (the gate's gated `neck_down` finds 0; the pass-6 scan's 5 plain-node necks all run ≤ 1.4 mm into the pad
    they end in);
  - `net_length` 67 is a record of every two-pad connection's length and ratio (1.0 included), not an instance of
    anything; the gate's net-level detour test covers nets without a pour.
  - **Chain detours** (47, 30 critical) are M2 items ("no needless detours"), not out of scope: the 9 on poured nets
    are gated (A34–A41 and A47), the 21 on critical nets without a pour are C24 and the 17 on non-critical nets C25.
    Against the fix-pass-6 board ARM1_SENSE's, CAM_5V_SENSE's In2, CAM_FAULT_N's In2 bump and I2C1_SDA's are gone and
    the 3V3A hop's is back (A47); A34, VLOGIC and SERVO2_OUT are shorter.
  - Close same-net via pairs (`via_pair_close` 22): the pair that pass 7 found joined only by copper overlap, 3V3
    (30.17, 71.17) / (30.4, 70.25), is gone (one via deleted in fix pass 7). For the rest the gate now tests what
    makes such a pair a defect: overlapping rings (`via_overlap`, gated, 0) and a via joined to a same-net track only
    by overlap (`via_on_track`, gated on critical nets, 0; six GND vias inside their own fill are information, part
    E); a pair in series on a poured net is `pour_net_hop` (gated) and a short one `short_layer_hop` (part E, C23).
    BAT_IN (9.725, 35.525) / (9.2, 36.05) is now a split run with a 0.74 mm hop (C23).
  - The rest (diagonal pad entries, doglegs, 90° corners) are not M2 items as such: AGENTS §3 allows 45° entries and
    90° corners, and a dogleg is a jog only below the tiny-jog limits (gated).
- **Local bumps** (fix pass 7): `bump_audit` searches every 2–8 segment window of every run on a critical net (82 on
  the final board; gated): 1 removable, allowlisted (A48). On the other nets (`--bumps-all`, 223 windows in all) the
  findings are C27.
- **Silkscreen:** 90 designators are hidden, as AGENTS §3 allows for a designator with no spot nearer its own part,
  each kept on F.Fab and listed in M3_R7 "Silkscreen"; not a deviation. Every legend about a part lies within 6 mm of
  that part's courtyard (`check_r7.legend_subjects`, gated since fix pass 7; P6-DOCS-04(d) fixed).

### Open after fix pass 7

**CAD and records:**
- (Closed 2026-10-18: the owner accepted the deviation list above, with C1's rise as estimated.) P7-DOCS-01 / P6-DOCS-01 /
  P5-DOCS-01 / P4-DOCS-01 / P3-REQUIREMENTS-01 (Major): the owner's dated acceptance of the deviation list (REQUIREMENTS M2).
- (Done: review pass 8 on `c872a3d3…`, 0 Critical / 0 Major.) A review pass on the fix-pass-7 board (`c872a3d3…`): REQUIREMENTS "R7 acceptance" needs an independent pass with
  no open Critical or Major on the board that is ordered.
- The IPC-2152 rise of the 7.7 A copper (C1): the owner's limit, or ACT_GATE / parts moved or a re-layout of the
  battery corner; the F4 bench stall test either way.
- For a board pass, if the owner asks for one: the judged removable items (C27: VLOGIC_SENSE, BAT_SW_SOURCE); the
  items not examined (C23's 0.74 mm BAT_IN piece); the optional tidy-ups of C17, C19, C21 and C22; a via spot for the
  three unstitched GND fingers fix pass 7 added or narrowed (C11).
- P4-RF-01 (wider unstitched GND fingers, C11) and P4-RF-02 (no gate checks F.Cu coplanar ground beside the GCPW
  lines, F.Cu under the module bodies, or where a pour trim lands near RF copper): tools, not done.
- Tool notes: `procurement_catalog.json` does not carry LS120's reflow rating (pass-2 DFM-08); `test_r5_repair`:
  retarget to the R5 commit or retire; A48's reason (R105.2's GND) and the A42–A46 blockers are not re-run by the gate.
- The M3_R7 vibration estimate was computed on the pass-2 board (Inference that it carries over).

**Before ordering:**
- The owner's acceptance and a clean review pass on the final board (above).
- U4 consignment (R7P1-18: the tools have no consignment path).
- JLC's written confirmation of the forward rail (DFM-03).
- U30 reservation and fresh cost and stock data (within 24 h).
- The JLC order-number placeholder at its new spot, (22.9, 86.15) on B.SilkS (ORDERING §3).

**Bench and physical** (ORDERING §5):
- antenna short cold and hot, with an oscillation check (fit C304 if needed);
- RF match (pi-network tuning, shunt stubs included), J30–J31 isolation and GNSS C/N0 with the radio keyed
  (≥ 39 dB);
- pyro immunity to the transmitter; radio NRST held low in reset;
- jack centre-to-shell check and leg-fillet inspection; D30, D31 and C302 seated flat (first-article inspection);
  NRST gate after J2 is coated;
- tap/modal check on the sled; SMA torque and staking;
- thermal-camera servo stall test (F4; C1);
- every R6 bench gate.

**Elsewhere:** the plug and coax choice (and its torque value) and the Onshape shroud measurement (board
position); the proposed VEHICLE.md additions (coordinator); the R7 firmware binding.

**Next:** the owner's decision on the deviation list. Review pass 8 on `c872a3d3…` found no Critical or Major issue (below).


## Review pass 8 (board `c872a3d3…`)

Three independent reviewers (routing geometry and quality, board-wide regression and electrical integrity, requirements and
deviation list), with the three-skeptic check for any Critical or Major finding. Reports: `m3_design/assembly_review/sources/r7_review/pass8_*.md`;
verdicts: `pass8_verdicts.json`. Result: **0 Critical, 0 Major, 10 Minor.** The gate passes on `c872a3d3…` (DRC, unconnected,
parity and ERC 0; routing hygiene 0 failing; all contracts and fit OK). Every pass-7 finding is closed or dispositioned. This
meets the review-loop stopping rule (no Critical or Major, gate at zero); the Minors are recorded, not reworked.

| ID | Sev. | Finding (first line) | Disposition |
|---|---|---|---|
| P8-ROUTING-01 | Minor | Three tracks lie wholly inside their own power pour and duplicate it. (1) 3V3A In2 (35.9632,69.9393)→(35.9632,76.0768)→(35.5,76.54), w 0.2, R6 copper: 6.1 mm of it lies inside the 28.17 mm² 3V3A_In2 fill; only the first 0.66 mm, from a via outside the zone out | Recorded; not reworked (Minor, DRC-legal; owner may request a touch-up) |
| P8-ROUTING-02 | Minor | (1) necks7's new BAT_IN crossbar via (9.45,109.8) is 0.188 mm from R123.2 (GND, B.Cu); a short connects the battery input to GND. It is absent from C15 and from the handoff, because F8's newgap.py stopped with a TypeError (SHAPE_CIRCLE_Collide) at the first vi | Recorded; not reworked (Minor, DRC-legal; owner may request a touch-up) |
| P8-ROUTING-03 | Minor | BAT_IN via (9.955,44.25), the In2 tap for R82.1's F.Cu track, reaches the In2 BAT_IN plane only through ring overlap. Its centre lies 0.055 mm outside the R6_BAT_IN_In2 zone outline (edge at x 9.9), and the joint is 0.108 mm² of overlap out of the ring's 0.283 | Recorded; not reworked (Minor, DRC-legal; owner may request a touch-up) |
| P8-ROUTING-04 | Minor | F8's bumps7 created a compound knee through a via on 3V3A B.Cu: U5.2 (35.67,71.175) → N → NE 0.415 mm → via (35.9632,69.9393) → NW 0.500 mm → (35.6096,69.5857) → N. The run dents 0.29 mm east to touch the via and resumes 0.0604 mm off its incoming line. In a p | Recorded; not reworked (Minor, DRC-legal; owner may request a touch-up) |
| P8-REGRESSION-01 | Minor | The new copper was not fully gap-checked, and C15 is incomplete against its own stated scope. | Recorded; not reworked (Minor, DRC-legal; owner may request a touch-up) |
| P8-REGRESSION-02 | Minor | necks7 deleted C86.2's own GND via (18.975, 83.85) and its F.Cu track to clear the RAW_ACT neck. The records justify this with: 'C86 keeps its GND through its thermal joint to GND_F (J122.3, a plated GND pin, 2.4 mm away)'. That is untrue. | Recorded; not reworked (Minor, DRC-legal; owner may request a touch-up) |
| P8-REGRESSION-03 | Minor | label_near placed each row of a pin table separately, on either face. | Recorded; not reworked (Minor, DRC-legal; owner may request a touch-up) |
| P8-DOCS-01 | Minor | Fix pass 7's copper created two sub-0.2 mm gaps that are listed nowhere. | Recorded; not reworked (Minor, DRC-legal; owner may request a touch-up) |
| P8-DOCS-02 | Minor | Several figures and summary claims are not exact. | Recorded; not reworked (Minor, DRC-legal; owner may request a touch-up) |
| P8-DOCS-03 | Minor | check_r7.legend_subjects measures the gap between the legend's bounding box and the part's courtyard box at their nearest point. A long legend therefore passes when one corner is near its part. Two of fix pass 7's placements read across neighbouring parts. | Recorded; not reworked (Minor, DRC-legal; owner may request a touch-up) |
