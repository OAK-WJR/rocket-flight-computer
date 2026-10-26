# R9 pass 2: RF layout, interface buses and coexistence review

Independent, read-only review, 2026-10-25. Dimension: RF. Review pass 2 of R9, on the board made by review pass 1's fix
pass.

- **Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `4f841a0e44ebb1829ad7996dfe6320ed527fce1fdb1e5ff11658e0705b44ac14`, hashed before and after this review: unchanged.
- **Other inputs, hashed at the start of the review:**
  - netlist `schematic.net.xml` `8b0e04ea…` and DRU `m3.kicad_dru` `ea77b791…`, both as pass 1 reviewed them;
  - `tools/check_r9.py` `d314215e…` (pass 1: `c38ad9a0…`), `tools/gcpw_solve.py` `fab2eef0…` (unchanged);
  - `m3_design/r9_rf.py` `881e7a2d…` (pass 1: `eb468064…`), `m3_design/r9_route_rf_if.py` `8d6f85aa…` (unchanged),
    `m3_design/r9_build.sh` `fefd7bbd…`.
- **`git status --porcelain` digest:** `052b2785…`, the same before and after the review, including after a full
  `tools/check.sh` run and the RF test suites.
- **Comparison boards, copied to the session scratchpad and deleted afterwards:**
  - pass 1's board `fc3d5b34…`, from the fix pass's own backup `r9review/orig/worktree_before_fix1.tgz`, with its
    `r9_rf.py`, `r9_route.py` and `check_r9.py`;
  - R7 (`git show 431025d`, `c872a3d3…`).

**Scope.** The RF strip as regenerated:

- congruence with R7's launch and chains;
- GCPW 50 ± 2.5 Ω by `gcpw_solve`;
- stitching and fence, keep-outs, chain order, and the limiter on B.Cu under U30;
- the interface buses from U1;
- F10's separations and the coexistence paths;
- the radio-to-pyro distance;
- the reset states of the radio and GNSS lines;
- the RF parts of the records.

Pass 1's RF findings are checked first, then the fix pass's changes are checked for regressions.

**Conventions.** Coordinates are KiCad mm, y = 0 at the aft (SMA) edge and +y forward. Stitching sides are named by
compass for a line run from the jack forward. **Inference** marks anything not measured and not taken from a maker
document.

## 1. Summary

**No Critical and no Major findings, and one Minor finding, not worth fixing now.**

**All three of pass 1's RF findings are closed (§2):**

- **R9P1-RF-01:** R7's three module ground vias are back, exactly at R7's spots in U31's frame.
- **R9P1-RF-02:** the records now name the stitching sides correctly, and the C303 stub text is right.
- **R9P1-RF-03:** R-5's attribution is now deterministic. This review's gate run reproduces the recorded
  `step10_evidence/gate/r9.json` and `route.json` exactly, apart from the two fields that `bind_report.py` adds.

**The fix pass caused no RF regression.** In the strip (y < 23) it changed only three things:

1. RADIO_TXEN, from 0.15 to 0.20 mm wide;
2. one grid via, moved from (24.70, 10.45) to (24.65, 10.45);
3. three new GND vias at R7's spots: (34.35, 15.27), (31.88, 10.40) and (28.07, 17.60).

The rest is unchanged:

- **RF line samples:** all 705 independent samples, every 0.025 mm along the four RF nets with the F.Cu gap scanned on
  both sides and In1 / In2 checked, are identical on `fc3d5b34…` and `4f841a0e…`.
- **Interface lanes:** identical but TXEN's width.
- **Strip ground reach:** F.Cu 2.99 mm, down from 3.10. The patch beside U31.7 went from 3.10 to 2.21 mm, against R7's
  2.12.

**R9P2-RF-01 (Minor, not worth fixing now):** no gate holds R7 pass 3's module-ground qualification, so the vias the
fix pass restored can be lost again without notice.

- This review removed the three restored vias from a scratch copy of the board and refilled it. check_r9 R-4 / R-5 /
  R-7 / R-8 / R-12 and `route_check --profile r9` still passed: strip reach 3.10 mm, against a limit of 4.0.
- The fix pass gave a reason for not adding the R-7 row: "a gate at exactly 0.35 mm on a 0.05 mm raster would sit at its
  limit". That reason does not apply to a geometric ring-to-pad measure, which is exact: 0.160 / 0.300 / 0.300 mm.

## 2. Previous pass in this dimension: closure

| Pass 1 finding | Fix pass disposition | On `4f841a0e…` (this review) |
|---|---|---|
| R9P1-RF-01 (Minor): U31's three ground pins lost R7's pin-adjacent GND vias | Fixed in copper (D-F1-02, `r9_rf.GND_MODULE`) | **Closed.** See below the table. |
| R9P1-RF-02 (Minor): records swap the R-7 sides; ORDERING §4's C303 stub text | Fixed in the records; R-7 evidence now east / west | **Closed.** See below the table. |
| R9P1-RF-03 (Minor): R-5's window attribution not deterministic | Fixed in the tool (D-F1-03: nearest pad, sorted designators) | **Closed.** See below the table. |

**R9P1-RF-01 closure.**

- **Vias at R7's spots:** at U31 (30.61, 14.0), rotation 180, U31-relative (+3.74, +1.27), (+1.27, −3.60) and
  (−2.54, +3.60). Each is 0.6 / 0.3 mm GND with pads on all four layers, offset 0.000 mm from R7's own vias in R7's U31
  frame (R7: (33.6, 15.27), (31.13, 10.4), (27.32, 17.6) about U31 at (29.86, 14.0)).
- **Ring to pad edge:** U31.2 0.160 mm, U31.7 0.300 mm, U31.16 0.300 mm, the straight path all in F.Cu GND copper. On
  the fix pass's raster this is 0.20 / 0.35 / 0.35 mm, R7's qualified figures.
- **Clearance to foreign copper:** 0.640 mm (U31.1 3V3_RADIO, U31.3), 0.716 mm (U31.6 RADIO_RF, U31.8 and U31.17 NC).
  Mask web to the own pad's opening ≥ 0.16 mm. None of the three is among the 23 own-net ring / opening pairs under
  0.1 mm (`fix1_measure` `via_openings`, C13).
- **Patch beside U31.7:** the patch west of RADIO_RF's last 0.7 mm is now 2.21 mm of copper from a via at (31.28, 8.13)
  (was 3.10 mm at (32.28, 8.13); R7 2.12 mm). It is no longer the strip's farthest point.

**R9P1-RF-02 closure.**

- **F10:** "2.38 / 1.75 mm on the GNSS east / west sides and 2.405 / 1.70 mm on the radio west / east sides, by compass".
- **The other records:** R9_VALIDATION's RF table and M3_R9 "RF strip" agree. Gate evidence: `GNSS_east 2.38`,
  `GNSS_west 1.75`, `RADIO_east 1.7`, `RADIO_west 2.405`.
- **ORDERING §4 l. 84:** "in R9, C303's trace joins the line at the bias-tap node, L30's antenna end, 0.95 mm before
  R304.1". This matches the board: C303.1 at (14.53, 6.18) and R304.1 at (13.59, 7.13).

**R9P1-RF-03 closure.**

- **This review's gate:** `tools/check.sh` exit 0. Its `r9.json` equals `step10_evidence/gate/r9.json` on every rule,
  with `board_sha256`, `inputs_sha256` and `checker_sha256` the same.
- **R-5's split:** GNSS C303 10, C305 10, L30 30, R304 32, launch 49, module 24; RADIO C313 10, C314 10, R316 34,
  launch 49, module 28; 286 in all.
- **`route.json`:** equal too, but for the binder's `board_sha256` / `bound_by`.

**Pass 1's observations O1–O6, re-checked on `4f841a0e…`:**

| Observation | Now |
|---|---|
| O1 F10 fast-line margin | Unchanged: R306–USB_DM 5.005 mm (gate R-10). This review's pad-to-copper measure gives 5.215 mm. |
| O2 parallel runs | Unchanged: interface lane copper is identical but TXEN's width. |
| O3 DIO1 / buzzer | Unchanged geometry. |
| O4 NRST fence opening | Unchanged: 2.50 mm. |
| O5 window impedance | Re-solved; see §4 O2. |
| O6 C310 thermal relief | Unchanged. |

## 3. Measurements

### 3.1 Gate and tools, run in this review

- **`NUMPY_PY=…/cfd/venv/bin/python3 tools/check.sh`:** exit 0 in 289 s.
  - DRC 0, unconnected 0, parity 0, ERC 0.
  - Metadata / 3D audit OK; silkscreen and fit OK.
  - check_r9 OK on all 40 rules, R-1 … R-13 included.
  - route_check r9: 0 failing, 0 allowlisted, 0 leftovers.
  - check_actuators OK.
  - Run on the repository board (kicad-cli reads it); the board SHA and the status digest were unchanged afterwards.
    The report folder was copied to scratch and deleted.
- **`python -m unittest test_r9_rf test_r9_check`** (KiCad Python): 69 tests OK in 446 s. These include the fix pass's
  R-7 'GNSS west' label test and the R-8 body-notch test.
- **`gcpw_solve.py --validate`:** coated 49.959 Ω (pass 2 50.3), bare 51.995 (52.2), launch 48.790 (49.0); OK within 1 Ω.

### 3.2 What the fix pass changed in the strip

Every track, via, footprint and zone was dumped on both boards and diffed (`dump_items.py`).

| Item | `fc3d5b34…` | `4f841a0e…` |
|---|---|---|
| RADIO_TXEN, 7 segments (2 F.Cu, 5 B.Cu) | 0.150 mm | 0.200 mm, same centrelines |
| GND grid via | (24.70, 10.45) | (24.65, 10.45) |
| GND vias at U31's ground pins | none | (34.35, 15.27), (31.88, 10.40), (28.07, 17.60), 0.6 / 0.3 |
| Strip vias (y < 23) | 194 | 197 (15 GND vias under U31's body, 14 under U30's) |

There is no other change at y < 23:

- every other strip part, track and via is identical;
- the zones and keep-outs are unchanged in outline;
- the fills changed only by the new vias.

The board totals are 583 vias, 345 at 0.5 / 0.3 and 238 at 0.6 / 0.3, as ORDERING §3 says. The fix pass's other copper
(QSPI_IO2, C98 / USB_LIMITED, the RAW_ACT vias, the ground aid's vias) all lies at y ≥ 41.

### 3.3 RF lines and GCPW

**Geometry and impedance:**

- **The lines:** W 0.30 mm on F.Cu.
  - GNSS: J30 (13.59, 0) → (13.59, 2.3 … 7.13) → the R304 jog → U30.11 (14.45, 9.3).
  - Radio: J31 (32.29, 0) → (32.29, 2.3 … 7.6) → the R316 jog → U31.6 (33.15, 9.05).
  - Both are R7's chains by template; R-6 measures GNSS 4.85 mm and radio 4.75 mm, two bends each.
- **Independent sampler (`rfline.py`):** every 0.025 mm on every RF track, 705 samples, with F.Cu copper scanned at
  0.005 mm and In1 at the centre, ±0.15, ±0.45 and ±0.70 mm.
  - Outside the chain windows, F.Cu GND sits 0.26–0.30 mm from the track edge on both sides (0.31–0.32 at the bends).
  - In1 GND covers ±0.70 mm everywhere but over the launch cut-outs (y < 4.6, by design); In2 GND is under every sample.
  - The result is **identical, sample for sample, to `fc3d5b34…`**.
- **Gate (`requalify_r9.json` `rf.gcpw` on `4f841a0e…`):** 79 line samples, gap pairs 0.26 / 0.26 to 0.32 / 0.32,
  Z0 50.16–51.08 Ω.

This review's solves (`gcpw_solve.z0`, coated, over In1):

| Gaps (mm) | Z0 (Ω) | Where |
|---|---|---|
| 0.26 / 0.26 | 50.165 | most line samples |
| 0.28 / 0.28 | 50.514 | most line samples |
| 0.32 / 0.32 | 51.077 | bend samples |
| 0.38 / 0.38 | 51.615 | stub and T edges |
| 0.555 / 0.555 | 52.268 | inside the U31.6 pad entry |
| 0.39 / 2.5 | 52.156 | GNSS y 6.6–7.1, east open |
| 1.25 / 1.29 | 52.631 | GNSS_RF_IN y 7.13–7.6 at R304.2 / C305's T; the radio T at R316 |
| 2.5 / 2.5 | 52.655 | the microstrip limit |

Sections at the chain parts, where one or both coplanar grounds open, reach 52.63–52.66 Ω. These are R7's windows, each
≤ 0.5 mm of line and within 0.3 mm of a chain pad (observation O2).

### 3.4 Launch congruence

- **check_r9 R-4:** both jacks have one In1-only cut-out at x ±0.9, y 0–4.6, and In2 GND under it with 0 missing. Via
  offsets are 0 / 0 / 0 / 0 / 0.02 / 0.02 / 0 / 0 mm against the qualified spots (R7's built y 3.58). The pad is
  0.301 mm from F.Cu GND.
- **`rf.launch`:** window GND copper XOR against R7's J31 is 0.0 mm² for both jacks, and J30 = J31.
- **`rf.r7`:** every chain part sits at R7's frame position, but the two recorded deviations, D30 turned and C303 at the
  bias node (D-S4-02). L30 is within 0.0005 mm (rounding).

### 3.5 Stitching, fence and strip ground

**R-7 on `4f841a0e…`:**

- **Stitching gaps:** GNSS east 2.38 / west 1.75 mm, radio east 1.70 / west 2.405 mm, all ≤ 2.5. They are unchanged:
  the new via at (31.88, 10.40) lies beyond the U31.6 pad entry, where R-7's range ends.
- **Fence:** 24 vias on y 22.2, with four lane openings: 17.25–19.40 (2.15), 20.95–23.05 (2.10), 23.05–25.20 (2.15) and
  38.80–41.30 (2.50), each crossed by its lanes.
- **RF ground pads:** vias 0.05–0.23 mm away.
- **Coverage:** F.Cu 77.8 %, In1 95.1 %, In2 96.7 %, B.Cu 92.9 %.

**Through-copper GND reach** in the strip, on route_check's raster (`reach_rf.py`):

| | `fc3d5b34…` | `4f841a0e…` |
|---|---|---|
| F.Cu, worst | 3.10 mm at (32.28, 8.13), beside U31.7 | 2.99 mm at (45.48, 3.53), the east edge, 12 mm from an RF line |
| F.Cu within 1.0 mm of an RF line centre, worst | 3.10 mm (radio, at U31.7) | 2.21 mm (radio, (31.28, 8.13)); GNSS 2.02 mm at (13.78, 8.78), beside U30.12 |
| B.Cu, worst | 3.57 mm at (0.53, 9.73) | 3.57 mm at (0.53, 9.73) |

u-blox IM §4.4 asks that "any stubs at the ground planes … be avoided or ended with a via". Measured:

- route_check finds no pour finger in the strip;
- no F.Cu GND point lies farther than 2.21 mm of copper from a via within 1 mm of an RF line;
- the strip's worst point is 2.99 mm.

### 3.6 Module grounding and the fills under the modules

| Pad | Nearest GND via, ring to pad edge (this review) | Raster reach (`fix1_measure`) | R7 |
|---|---|---|---|
| U31.2 | (34.35, 15.27), 0.160 mm | 0.20 | 0.20 |
| U31.7 (beside ANT) | (31.88, 10.40), 0.300 mm | 0.35 | 0.35 |
| U31.16 | (28.07, 17.60), 0.300 mm | 0.35 | 0.35 |
| U30.1 | (5.97, 18.54), 0.130 mm | 0.20 | 0.85 |
| U30.10 | (16.35, 8.50), 0.150 mm | 0.20 | 0.60 |
| U30.12 | (13.50, 11.00), 0.500 mm | 0.55 | 0.75 |

GND fill under the module interiors, sampled every 0.1 mm (`undermod.py`):

| Module | F.Cu | In1 | In2 | B.Cu |
|---|---|---|---|---|
| U30 | 98.3 % (misses at the pad clearances) | 100 % | 100 % | 82.4 % (the limiter, as designed) |
| U31 | 97.5 % | 100 % | 100 % | 100 % |

This meets u-blox IM §4.4 ("ground the area below the module, on the top and second layer") and EBYTE §4.1 ("copper is
laid on the Top Layer … well grounded").

### 3.7 RADIO_TXEN at 0.2 mm

- **R-2:** B.Cu length in the strip 22.719 mm (R8 22.72), the same centrelines as before.
- **Clearances:**
  - the west run (x 25.25) is 0.26 mm outside U31's B.Cu body keep-out (x ≥ 25.61; was 0.285);
  - the moved grid via is 0.200 mm away, ring to track;
  - the nearest copper otherwise is the GND fill at its 0.15 mm zone clearance, and the partner via (32.48, 20.55) ring
    to ring 0.172 mm, unchanged.
- **GND partners:** both TXEN vias have one within 0.721 mm.
- **Reference:** In2 GND under every TXEN B.Cu sample but within 0.6 mm of its own two vias (antipads).
- **R-11:** TXEN copper 8.95 mm from U30's body.
- **EBYTE §4.1:** the loop runs on the bottom layer at the module's digital (west) side, outside its body, with full
  top-layer GND under the body. This is the routing EBYTE allows.

### 3.8 Keep-outs

check_r9 R-8 on `4f841a0e…`:

- U30_KEEPOUT (F.Cu, In1 6.1–16.2 × 10.35–17.75) and U31_KEEPOUT (F.Cu / In1 interior 26.56–34.66 × 9.95–18.05;
  In2 / B.Cu body 25.61–35.61 × 9.0–19.0) leave 0 mm² of the derived regions uncovered.
- GND fill is present at all 2,601 samples under U31's whole body on In1, sampled over the whole body since D-F1-03, and
  on In2, and at 1,938 under U30's keep-out on In1.
- No non-GND track or via lies inside. The three new vias are GND, which the keep-outs and EBYTE allow.

### 3.9 Chain order and the limiter

- **R-9:**
  - ESD 0.795 mm from each jack pad end;
  - C302 0.925 mm from L30's cold pad;
  - stubs 0.94 mm;
  - order jack → ESD → bias tap → pi → module.
- **Limiter:** on B.Cu under U30, copper unchanged by the fix pass.
  - VCC_RF, ANT_DC and LNA_EN change layer at V1 (10.4, 7.4), V3 (11.3, 7.4) and V2 (12.25, 7.4), each with a GND
    partner within 1.5 mm (route_check critical_via_no_gnd clean).
  - route_check r9 reports only information instances on the RF-family nets: the TXEN u-turn; the RXEN / RESET_N extra
    bends; the NRST u-turn; LNA_EN's end 0.15 mm short of Q31.1 (D-S4-03 / D-S9-01); the pad entries.
  - There is no detour and no allowlist entry: no A2 / A3.

### 3.10 Interface buses U1 → strip

`lanes.py`: every RADIO_* / GNSS_* track but the RF lines, with In1 GND (F.Cu) or In2 GND (B.Cu) sampled at the centre
and ±(w/2 + 0.1) every 0.05 mm, on both boards.

| Net | Copper | Vias | Reference |
|---|---|---|---|
| RADIO_SCK / _MCU, MOSI / _MCU, MISO / _MCU | 14.18 + 13.72, 17.09 + 8.13, 1.48 + 25.95 mm F.Cu | 0 | full |
| RADIO_NSS / BUSY / RXEN / DIO1 / NRST | 29.73 / 30.06 / 36.89 / 26.49 / 45.76 mm F.Cu | 0 | centre full |
| GNSS_TXD / _MCU, RXD / _MCU, TIMEPULSE / TP_MCU, RESET_N, SAFEBOOT_N | 2.13 + 20.37, 14.37 + 8.54, 2.13 + 21.95, 20.40, 4.87 mm F.Cu | 0 | full |
| RADIO_TXEN | 2.45 F.Cu + 22.72 B.Cu | 2 | full but at its own vias |
| GNSS_LNA_EN / VCC_RF / ANT_DC | 1.90 F + 2.40 B / 2.21 F + 2.55 B / 2.33 F + 1.75 B | 1 / 1 / 1 | full but at their own vias |

- **NSS and NRST edge samples** (one side, w/2 + 0.1 mm off the centre; the centres are covered): NSS has 7 at
  (23.25, 27.4–27.7), beside R310's 3V3 via. NRST has 18 at (32.9–33.45, 42.8–44.2), inside a foreign via antipad. Both
  are as pass 1 found them.
- **Unchanged:** every lane is identical on `fc3d5b34…` (TXEN differs only by its width), so pass 1's crosstalk and
  coexistence figures stand.

### 3.11 F10 separations and coexistence

**Gate (R-10, R-11, R-12):**

- **Separations (R-10):** nearest RF part to a restricted part R313–U1 6.04 mm (≥ 5.94, hard X9); nearest fast line
  R306–USB_DM 5.005 mm (≥ 5.0).
- **Coexistence (R-11):**
  - radio copper to U30's body: RXEN 5.2, BUSY 5.7, MISO_MCU 6.2, MOSI 7.3, NSS 7.75, SCK 8.35, TXEN 8.95 mm;
  - module courtyards 7.67 mm apart;
  - GNSS RF to radio RF copper 15.46 mm.
- **Supply (R-12):** C311 1.97, C312 2.191, C310 3.639 mm (U31.1); C301 2.13, C300 2.556 mm (U30.7 / 8); GNSS VCC path
  0.088 Ω.

**Independent (`dist.py`, courtyard to courtyard):** R313–U1 6.04, R310–U1 6.24, R315–U1 6.24, R306–U1 6.29 mm. The
nearest USB / QSPI / HSE copper to an RF part pad is R306.2 at 5.215 mm.

ORDERING §5 carries the coexistence bench step:

- C/N0 per band;
- UBX-MON-SPAN with max hold;
- a radio-asleep condition and a reference receiver;
- the HSE's 1575.000 / 1175.000 MHz harmonics and the radio crystal's 1184 / 1568 MHz;
- a repeat with the buzzer sounding.

### 3.12 Radio to pyro

- **check_r9 R-13:** 46.13 mm (U31 courtyard to Q124.5, PYRO1_OUT), ≥ 40.
- **Independent (`dist.py`):**
  - U31 to armed copper 46.13 mm;
  - U31 to J121 49.18 and to J124 59.27 mm;
  - J31 to armed copper 61.84 mm;
  - radio RF copper to armed copper 58.23 mm;
  - U31 to any PYRO1_ / ARM1_ copper 26.89 mm (R170, the MCU-side sense resistor).
- **Records:** F10 and ORDERING §5 make the keyed-radio immunity test a required gate before any flight (owner
  decision 3). It is not yet run.

### 3.13 Reset states and the module pin contract

The netlist is unchanged since pass 1 (`8b0e04ea…`), so the U1 map (check_r9 K-contract) and R8 pass 4 §4.7's datasheet
analysis carry over. This review re-read the netlist:

- **Radio:** R311 2 k NRST → GND, R312 100 k RXEN → GND, R310 100 k NSS → 3V3, R313 / R315 33 Ω at the MCU end and R314
  33 Ω at the radio end, TXEN = U31.9 + U31.19 (DIO2).
- **GNSS:** R305 / R306 220 Ω and R307 1 k; RESET_N to U1.61 (PD14, open drain in the binding note) with no capacitor;
  SAFEBOOT_N on TP30 only.

The MAX-F10S pins against the u-blox IM UBXDOC-963802114-12892 R01, Table 1 and §3.2.3:

- V_BCKP (pin 6) is open: "leave open if no external backup supply".
- VIO_SEL (pin 15) is open, which selects 3.3 V.
- EXTINT, SDA and SCL are open: "if not used, leave open"; the inputs have internal pull-ups.
- RESET_N has no capacitor: "no capacitor should be placed at RESET_N to GND".
- TIMEPULSE reaches only R307 → PD15, which is analog and high-Z after MCU reset. The IM: "if this pin is low at receiver
  startup, the receiver will enter safeboot mode … make sure this pin has no load that could pull it low at startup".
  The binding note keeps PD15 as TIM4_CH4 input capture.

The E22-900MM22S pins against the EBYTE manual ch. 3:

- GND is pins 2, 7 and 16, now each with a via;
- NC pins 4, 5, 8 and 17, and DIO3 (18), are unconnected;
- TXEN is driven by DIO2, which ch. 4.2 allows;
- RXEN is pulled down; NRST is held low by R311 while PE9 is high-Z.

### 3.14 Records checked

- **REQUIREMENTS F10 (R9 clause):** stitching sides, fence, separations, R-13 46.13 mm against R8's 65.98 mm, and the
  bench gates. All match.
- **M3_R9 "RF strip":** matches, including U31's pins 0.20 / 0.35 / 0.35 mm and TXEN at 0.2 mm.
- **R9_VALIDATION "RF (F10)" table:** matches the gate and `requalify_r9.json` on `4f841a0e…`.
- **R9_VALIDATION "Review pass 1" rows RF-01 … -03:** match.
- **ORDERING §3:** impedance, stack-up, the narrowest track 0.2 mm and the via sizes match.
- **ORDERING §4:** the C303 text and the DNP land rules match.
- **ORDERING §5:** the RF bench items, coordinates and aggressor distances match.
- **STATUS R9 section and AGENTS §1 RF row:** match.

## 4. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R9P2-RF-01 | Minor (not worth fixing now) | r9_plan §1 graft "RF chains and modules congruent with R7, regenerated by template"; F10's R9 clause ("check_r9 holds the strip by rule, not by hash"); R7 pass 3 §3.6 (ground at the module pads); EBYTE manual §4.1 ("the module must be reliably grounded") | **No gate holds the module-ground qualification, so the vias the fix pass restored can be lost again without notice.** U31.2 / 7 / 16's vias, and U30.1 / 10 / 12's grid vias, exist only as table rows in `r9_rf.GND_MODULE` / `GRID`. No checker refers to them. R-7's strip reach (≤ 4.0 mm) is the only related rule, and it passed pass 1's regressed board at 3.10 mm. The fix pass's reason for not adding the R-7 row ("a gate at exactly 0.35 mm on a 0.05 mm raster would sit at its limit") applies only to that raster metric. | Scratch copy of `4f841a0e…` with (34.35, 15.27), (31.88, 10.40) and (28.07, 17.60) removed and natively refilled: `check_r9 --only R-4,R-5,R-7,R-8,R-12` all OK (R-7 F.Cu reach 3.10 mm); `route_check --profile r9` 0 failing. `grep` of `tools/` and `m3_design/` finds no rule naming the module vias (`r9_rf_check.py` gates frames, chain parts, launches, check_r9, GCPW, route_check, DRC and corridors). `fix1_handoff.md` §3 "Not done". The geometric ring-to-pad figures are 0.160 / 0.300 / 0.300 mm (§3.6). | At the next checker change, add an R-7 evidence row: each module GND pad's nearest GND via, ring to pad edge, geometric. Limits: U31.2 / 7 / 16 ≤ 0.40 mm (R7 0.16 / 0.30 / 0.30); U30.1 / 10 / 12 ≤ R7's raster 0.85 / 0.60 / 0.75 mm, or the same geometric metric at ≤ 0.6 mm. Add a seeded test that deletes one U31 module via. Re-pin check_r9's hash where the records bind it. The board needs no change. |

## 5. Observations (no finding)

**O1. F10 fast-line margin (carried from pass 1).** R306–USB_DM is 5.005 mm against 5.0 (gate R-10); C13 lists it. The
owner's 98 mm option (C1, reclassifying R306 / R310 / R313 / R315) would remove the question.

**O2. Window sections slightly above 52.5 Ω.**

- r9_plan's done row reads "GCPW 50 ± 2.5 Ω at every sample", and R-5 defines a sample as a line sample outside the
  windows. Those all solve to 50.16–51.08 Ω.
- Inside the windows, at R304.2 / C305's T, at R316, and beside L30 / C303 / R304, one or both coplanar grounds open to
  about 1.25–2.5 mm. gcpw_solve gives 52.16–52.66 Ω there, up to 0.16 Ω over 52.5, over ≤ 0.5 mm per window.
- R7 had the same windows. The effect on |S11| is about 0.003 at 1.6 GHz (Inference: |Γ| ≈ 0.026 over βl < 0.03 rad),
  inside D-S10-02's cascade, which is itself an Inference.
- The records say "line samples", so they are accurate. No action.

**O3. DIO1 next to the buzzer (carried).** RADIO_DIO1's diagonal passes 0.36 mm from the corner of LS120.2 (BUZZ_OUT).
The coupling is a few millivolts (Inference, pass 1). ORDERING §5's coexistence step repeats with the buzzer sounding.

**O4. NRST fence opening (carried).** 38.8–41.3, 2.50 mm, the widest, within R-7's 2.7 mm.

**O5. U31.7's pre-fix figure is quoted three ways.** The pre-fix value of U31.7's copper path is given as 1.12 mm
(D-F1-02), 1.10 mm (M3_R9) and 1.095 mm (R9_VALIDATION, `fix1_measure`). Pass 1's `padreach.py` gave 1.116. These are two
tools on one board; no action.

**O6. Two metrics for the coexistence distances.** `requalify_r9.json` `rf.separations` measures track copper only:
DIO1 16.85 mm, NRST 19.26 mm, as quoted in R9_VALIDATION's coexistence row. check_r9 R-11 includes pads: DIO1 16.5 mm
(U31.20), NRST 18.61 mm (U31.3). Both are far over 5.0 mm, and the record quotes its cited source correctly.

**O7. F10's isolation basis.** F10 bases ≥ 39 dB on the MAX-M10S's −17 dBm. The MAX-F10S IM §4.3.2 says "MAX-F10S
out-of-band immunity data are currently not available", and its Appendix A.1 (hardware changes) gives an absolute
maximum RF input power of 0 dBm for the MAX-F10S and MAX-M10S. R7 settled this (R7_VALIDATION E6: "the bench C/N0 test with the radio keyed is the
evidence for the MAX-F10S"). The 39 dB target covers the 0 dBm absolute maximum (22.3 dBm − 39 dB = −16.7 dBm). No
action.

## 6. Inferences (not measured, or not from a primary source)

- The |S11| effect of the window sections (O2) and the coupling estimates carried from pass 1 (O3).
- Unchanged from pass 1 and R8 pass 4:
  - spur levels;
  - the E22's NRST internal pull-up, which the ORDERING §5 reading at R311.1 settles;
  - Q30's thermal bound (D-S4-03);
  - the return-loss cascade's parasitics (D-S10-02).

## 7. Sources

- **u-blox MAX-F10S Integration manual** UBXDOC-963802114-12892 R01:
  - Table 1 (pin assignment: V_BCKP "leave open if no external backup supply", VIO_SEL, EXTINT / SDA / SCL "if not used,
    leave open", SAFEBOOT_N tied to TIMEPULSE through 1 kΩ);
  - §3.2.3.1 RESET_N ("no capacitor should be placed at RESET_N to GND");
  - §3.2.3.3 TIMEPULSE ("if this pin is low at receiver startup, the receiver will enter safeboot mode");
  - §4.1.3 V_BCKP; §4.2.3; §4.3.2 (out-of-band immunity data not available);
  - §4.4 "Layout" pp. 66–67 (5 mm to any RF component; GND stubs avoided or ended with a via; ground under the module on
    the top and second layer; CPW with ground on layer 2);
  - Table 42 (L4 47 nH LQG15HS47NJ02, or > 500 Ω at L1 / L5);
  - Appendix A.1 (absolute maximum RF input power 0 dBm, MAX-F10S and MAX-M10S; "do not drive the TIMEPULSE pin low at
    startup because it will put the receiver in safeboot mode").
  - https://content.u-blox.com/sites/default/files/documents/MAX-F10S_IntegrationManual_UBXDOC-963802114-12892.pdf
- **EBYTE E22-900MM22S product specification** (LCSC C5333985):
  - §2.1 (blocking power 10 dBm); §2.2 (32 MHz passive crystal; 10 × 10 × 2.5 mm, 1.27 mm stamp holes);
  - ch. 3 pin table (GND 2 / 7 / 16, NC 4 / 5 / 8 / 17, TXEN "MCU IO or DIO2, high level effective", RXEN high level
    effective);
  - §4.1 (reliably grounded; routing under the module only on the bottom layer with grounded top copper);
  - §4.2 (DIO2 to TXEN).
  - https://datasheet.lcsc.com/datasheet/pdf/70331b0eaf0eedaea0129e9e66d9a011.pdf?productCode=C5333985
- **Semtech SX1261/2 DS Rev 1.2:** Table 8-3 and Table 3-10, as verified in `sources/r8_review/pass4_rf.md` §4.7 (the
  netlist is unchanged).
- **Project records:**
  - `pass1_rf.md`, `fix1_handoff.md`, `fix1_progress.md`, `fix1/fix1_measure_4f841a0e.json`;
  - `docs/R9_VALIDATION.md`, `docs/M3_R9.md`, `docs/REQUIREMENTS.md` F10, `docs/ORDERING.md` §3–§5, `STATUS.md`,
    `AGENTS.md` §1 / §3;
  - `R9_DECISIONS.md` D-S1-03 / 04 / 05 / 10 / 19 / 22, D-S3-04, D-S4-01 … 08, D-S7-02 … 04 / 14, D-S8-19, D-S10-02 / 18,
    D-F1-02 / 03;
  - `step10_evidence/requalify_r9.json`, `gate/r9.json`, `gate/route.json`, `build_sha256.txt`, `tests.txt`;
  - `docs/R7_VALIDATION.md` E6.

## 8. Method (reproduction)

All scripts ran read-only under KiCad 10.0.6's Python. They were written in the scratchpad (`r9review/rf2/py/`) and run
on copies of `4f841a0e…`, of `fc3d5b34…` (from the fix pass's backup) and of R7 (git 431025d):

- `dump_items.py`: every track / via / footprint / zone, diffed old against new.
- `strip_parts.py`: strip parts and pads.
- `rfline.py`: the GCPW gap sampler (705 samples) with In1 / In2 checks, old and new compared.
- `modgnd.py`: module GND pads to the nearest via, and the new vias' clearances and mask webs.
- `r7vias.py`: the module vias in U31's frame on R7 and R9.
- `reach_rf.py`: strip GND reach on route_check's raster, old and new.
- `undermod.py`: GND fill under the modules.
- `txen.py`: TXEN's clearances, old and new.
- `lanes.py`: interface lanes and their references, old and new.
- `dist.py`: separations, radio to pyro.
- `seed_drop.py`: the three module vias removed from a copy and refilled; then `check_r9 --only R-4,R-5,R-7,R-8,R-12`
  and `route_check --profile r9` on it.
- `gcpw_solve.z0` on the gap pairs.

**Netlist:** `schematic.net.xml` parsed for U30 / U31 and the 32 RF-family nets.

**Gate:** `NUMPY_PY=… tools/check.sh` on the repository board. Its reports were compared with
`step10_evidence/gate/r9.json` and `route.json`, then deleted.

**Datasheets:** pdftotext of the u-blox IM and the EBYTE specification, each downloaded into its own scratch folder.

**Clean-up:** the scratch folder (board copies, downloads, scripts, reports) was deleted afterwards. Nothing in the
repository was written but this report. The board SHA and the status digest were unchanged.
