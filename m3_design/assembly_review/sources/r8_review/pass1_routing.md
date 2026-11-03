# R8 review pass 1: routing simplicity and geometry (whole board)

Reviewer: independent, read-only. Dimension: the geometry and simplicity of every track and via on all four layers, rigid
R7 copper included. Covered: AGENTS §3 rule instances, staircases, jogs and knees, local bumps, detours and extra vias,
bus tidiness, pad entries, width discipline, layer discipline (no signal on In1 / In2 except D70), and, for every remaining
exception, whether a DRC-clean edit removes it.

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `429b6db4dc95c1a0fd3e736625c416c20fa0e7fc72f6f6c9c576003340dc1987`. The SHA was the same before and after this review.
- **Contents:** 797 tracks, 608 vias (427 GND; 315 × 0.6 mm and 293 × 0.5 mm), no arcs.
  - F.Cu: 411 tracks, 1,226.5 mm.
  - B.Cu: 385 tracks, 868.2 mm.
  - In2: 1 track, 3.4 mm (ARM1_SENSE, rigid, D70).
  - **In1: none.**
- **Copper identical to R7:** 93 tracks and 189 vias, matched by net, layer, width and end points against `c872a3d3…`.
  This is the rigid RF strip, the CH1 block and the strip GND.
- **Gate on this board** (`tools/check.sh`, run by me, exit 0):
  - DRC 0, unconnected 0, parity 0, ERC 0.
  - Metadata / 3D audit OK; silkscreen 0; R8 CAD contract OK; actuators OK; fit OK.
  - route_check: "routing hygiene: 0 failing, 3 allowlisted, … 0 removable local bumps on critical nets (22 bump windows
    searched): OK".
  - `tools/test_route_check.py`: 57 tests OK.
- **Repository changes:** none except this file.
- **Scratch:** `<scratch>/r8p1rt/` (the session scratchpad),
  called `<s>` below.
  - Variant boards were saved only under `<s>/v/<name>/`, in a copy of the project.
  - They were deleted after their results were logged (`<s>/logs/`).

## 1. Verdict

The R8 routing reads as deliberate, simple and logical:
- **Buses:** the U1 river to the RF strip, the servo bus, the pyro corridor, the QSPI and IMU fans and the SWD / USB lanes
  are drawn as parallel lanes at constant pitch, with 45° mitres.
- **Segments:** no off-angle segment, arc, staircase, exposed acute angle, stub, dangling end or via, unmerged run, or
  duplicate or overlap-only copper anywhere on the board. The shortest interior segment of any new chain is 0.566 mm, a
  0.4 mm 45° mitre.
- **Width:** every new signal track is 0.2 mm, except the actuator gate family (0.25 mm, consistent within the family).
- **Layers:** In1 carries no track, and In2 carries only D70's rigid 3.4 mm.
- **Records:** the visible jogs, hooks and U-turns are each forced by a pin order, a keep-out, a rigid via or a placement
  constraint, and nearly all are explained in R8_DECISIONS or the generator comments.

**No Critical and no Major.** Four Minor findings:

- **R8P1-ROUTING-01 (Minor, worth fixing).** HSE_OUT folds back through its via.
  - The F.Cu run passes 1.15 mm beyond Y1.3, which is on the other side of the board, to a via on the crystal's far side,
    and B.Cu comes back into the pad.
  - Moving the via between Y1.3 and C26.1, plus one GND via, is DRC- and gate-clean with route_check's instance list
    unchanged. HSE_OUT goes from 9.27 to 7.36 mm (HSE_IN is 4.69 mm), the fold disappears, and the board's
    critical-reference unreferenced share falls from 11.57 % to 10.98 %.
- **R8P1-ROUTING-02 (Minor, worth fixing).** Three pad entries on large pads are untidy, and route_check's pad test never
  sees them (it skips pads over 2 mm).
  - U9.5 (BAT_IN): the track ends exactly on the pad boundary.
  - C75.2 (GND): the stub ends exactly on the pad boundary, 0.1 mm off the pad's axis, from a stale table coordinate.
  - C75.1 (CAM_5V): the 0.8 mm bar is 0.35 mm off-axis and overhangs the pad's inner edge by 0.25 mm.
  - R8_VALIDATION E's "by up to 0.85 mm" is therefore incomplete. A clean variant fixes U9.5 and C75.2.
- **R8P1-ROUTING-03 (Minor).** The VLOGIC sense tap uses a 0.6 mm power via, (26.95, 60.5), for a µA divider, and it sits
  at the 0.151 mm DRC minimum from the SERVO1_MCU lane (an MCU pin). A 0.5 mm via gives 0.200 mm and is clean. The other
  supply-net gaps at the minimum are listed; the USB_LIMITED / CAM_PWR_EN one is pinned by TP73's 1.0 mm zone, verified.
- **R8P1-ROUTING-04 (Minor, worth fixing).** Cross-layer fold-backs (a run that passes its target on one layer and comes
  back on the other) are neither gated nor listed.
  - My scan finds 26. Nine are on critical nets. Five of the nine are forced or recorded: A2, A3, C5 and the two rigid CH1
    exit vias.
  - **HSE_OUT** is removable (finding 01).
  - **QSPI_IO2 / IO3** (U3's outer-end via scheme) and **SPI1_MISO / MOSI** (the IMU's fixed orientation) are deliberate,
    but their reasons sit only in D54 or in the generator comments. They are not in R8_VALIDATION part C, which M2 requires
    for every review-only residual.

This is pass 1 on R8, so there is no previous R8 finding to close. §3 re-checks the four R7 pass-8 routing classes on R8;
none recurs as such.

## 2. Method

Scripts are in `<s>/`. Every one runs in KiCad 10.0.6's Python and loads boards read-only. Variants were written only
under `<s>/v/`.

| Script | What it does |
|---|---|
| `inv.py` | Track, via and zone inventory per layer, width and net; inner-layer tracks |
| `runscan.py` + `rg/scan.py` | The pass-2 reviewers' scan, unchanged, run on R8, with every instance attributed to R7-identical (rigid) or R8-new copper |
| `r8scan.py` | **My independent scan, written for this pass.**<br>- Node graph per (layer, net) at 1 µm, chains between non-plain nodes.<br>- Off-angle (> 0.01°), zero-length and open short segments; dangling, fill-only and overlap-only ends.<br>- Knees: every window in which a chain returns to its heading, with its lateral offset and middle length.<br>- U-turns, acute and right-angle corners, collinear and width-step plain nodes.<br>- Pad entries (direction against the pad's axes, offset); tracks over 80 % inside their own non-GND fill.<br>- Vias: layers joined by track, pad, fill or ring only; GND distance; via on a track body.<br>- Per-net widths, layers, vias and pad MST |
| `entry.py`, `padedge.py` | Pad-exit direction relative to the footprint (outward, lateral, inward, diagonal); track ends lying on a pad boundary (depth under 0.03 mm) |
| `viaturn.py` | **Fold-backs through vias:** each pair of arms of a non-GND via on different layers that leave it within 45° of each other, with the overlap length |
| `dent.py` | Bends and compound knees through via nodes on one layer (the P8-ROUTING-04 class) |
| `gndtrk.py`, `gaps.py` | GND track ends and fill coverage; edge gaps under 0.2 mm between supply-net copper and any other net, per layer |
| `bumps_all.py` | route_check's own `bump_audit` run on every non-GND net (the gate runs it on critical nets only) |
| `variant.py`, `vrun.sh` | Apply an edit list to a copy of the board in a copy of the project, refill natively, save to `v/<name>/`, then run `kicad-cli pcb drc --severity-all --schematic-parity`, `route_check --profile r8`, `check_r8` and `check_actuators`. Variant `base` (no edit): DRC 0/0/0, every check OK, route_check identical to the gate, so the refill matches |
| `rcdiff.py`, `tools/reference_audit.py` | route_check instance diff from `base` to a variant; critical-reference audit on `base` and on the variants |

I also rendered every region at 50–90 px/mm (`<s>/img/*.png`, made with `rg/render.py`) and read each one.

## 3. Previous findings in this dimension

There is no earlier R8 pass. The four R7 pass-8 routing classes, re-checked on R8:

| R7 pass 8 | Class | On R8 |
|---|---|---|
| P8-ROUTING-01 | A track lying inside its own power pour (duplicate copper) | **None.** `r8scan` finds no non-GND track ≥ 0.3 mm that lies more than 80 % inside its own fill on its own layer |
| P8-ROUTING-02 | A sub-0.2 mm supply adjacency that a trivial edit avoids | 32 supply-net gaps under 0.2 mm, all ≥ 0.151 mm (DRC legal). One next to an MCU pin net is avoidable (R8P1-ROUTING-03); one is forced by TP73's 1.0 mm zone (verified, §6) |
| P8-ROUTING-03 | A via joined to its plane only through its ring | **None on a non-GND net.** Four GND vias overlap the In2 GND fill only with their ring: (17.125, 57.375), (35.2, 55.05), (20.5, 61.6) and (33.05, 69.8). Each is solid to the In1, F.Cu and B.Cu fills, so the In2 joint is irrelevant |
| P8-ROUTING-04 | A compound knee through a via node | **None** (`dent.py`). There are seven bends at a via node on one layer, all plain 45° / 90° turns |

## 4. Whole-board scans

### 4.1 Independent scan (`r8scan.py`; R8-new / rigid)

| Category | New | Rigid | Notes |
|---|---:|---:|---|
| off-angle (> 0.01°) / arcs / zero-length | 0 / 0 / 0 | 0 | `rg/scan.py` finds 5 rounding-level instances (≤ 0.00014°, 0 µm lateral) |
| open short segments (< max(w, 0.2 mm), not inside a pad or via) | 0 | 0 | rg/scan's two are one 0.184 mm piece inside C301.1 and one rigid 0.2 mm piece at a via |
| interior chain segment < 0.5 mm | **0** | 2 | shortest new is 0.566 mm; rigid: TXEN's 0.424 mm mitres |
| dangling / overlap-only ends | 0 / 0 | 0 | |
| fill-only ends | 1 | 0 | BAT_IN B.Cu (41.25, 102.4), the feed's end in its own B.Cu pour, under route_check's 1.0 mm pour-stub limit |
| acute corners at plain nodes | 0 | 0 | three 45° pairs, each at a pad (Q30.2, C98.1, rigid R133.1) |
| right-angle corners | 59 | 3 | allowed by AGENTS §3; mostly U1 escapes and the SWD / USB entries (§5.6) |
| knees (the run returns to its heading) | 61 | 1 | §5.1 |
| U-turns | 5 | 2 | exactly R8_VALIDATION E's seven |
| collinear / width step at a plain node | 1 | 0 | CAM_INPUT_LIMITED B.Cu (35.0, 31.65), 0.25 to 0.5 mm, 0.45 mm from U7.5: the neck at a 0.25 mm WSON pin (E, `width_change_junction`) |
| tracks inside their own non-GND fill | 0 | 0 | |
| via on a same-net track body / one-layer via | 0 / 0 | 0 | |
| via fold-backs (`viaturn.py`) | 22 | 4 | §5.2 |

### 4.2 Reference scans

- **`rg/scan.py`** (unchanged), new / rigid: dogleg 41 / 1, chain_detour 24 / 3, right-angle corner 59 / 3, u_turn 5 / 2,
  pad_entry_diagonal 42 / 9, extra_bends 4 / 0, short_layer_hop 2 / 0, collinear_unmerged 1 / 0.
  - Every dogleg has a middle of at least 0.5 mm and a lateral offset of at least 0.4 mm.
  - None is a tiny jog (`rg/scan` tiny_jog: 0).
- **route_check** on this board: 96 instances = 3 allowlisted (A1–A3) + 93 information. Their categories and counts
  equal R8_VALIDATION E.
- **route_check `bump_audit` on every non-GND net** (`bumps_all.py`): 29 windows, one candidate.
  - The candidate is on BAT_ENABLE: F.Cu (17.4, 98.45) → (40.42, 93.5), 32.93 mm, against a 25.73 mm redraw.
  - **It is false.** The window's x 42.9 leg passes through TP84.1 and C87.1, both on BAT_ENABLE, so the redraw would
    leave both pads unconnected. The tool treats a run through a same-net pad as plain.
  - On a critical net this only produces a false "removable" report, so it fails safe. Note for the build-integrity
    reviewer (§8).

## 5. Topic by topic

### 5.1 Knees, jogs and steps

There is no tiny jog (a middle under 0.5 mm, or under 0.25 mm lateral). The knees under 1 mm lateral, each checked
against its cause:

| Net(s) | Where | Lateral / middle | Cause | Recorded |
|---|---|---|---|---|
| RADIO_RXEN / BUSY / MISO_MCU | x 20.6 / 21.1 / 21.6 → 21.0 / 21.5 / 22.0, y 22.0–22.8 | 0.40 / 0.566 | Below the fence the trio needs a 1.0 mm slot for the fence via (22.1, 23.3) between MISO and MOSI (D16's 2.7 mm openings). Inside the strip the slot would leave an unstitchable GND finger, because strip GND is rigid | `r8_route_rf.py` comment |
| RADIO_SCK | x 25.1 → 24.5, y 21.8–22.4 | 0.60 | R313 at x 25.1 against U31.15's approach outside the module body (x ≤ 24.6) | comment |
| RADIO_DIO1 | x 32.85 → 32.4, y 30.45–30.9 | 0.45 | The nested east-face escapes (NSS 31.65, SCK 32.25) against U31.20 at x 32.4; closes a GND finger at NRST's turn | comment |
| QSPI_IO3 | (24.5, 38.45) → (24.0, 38.95) | 0.50 | Clears IO1's via (25.0, 39.4) by 0.65 mm instead of 0.15 mm. A straight drop to (24.5, 40.58) joins the same diagonal (0.41 mm shorter, two bends fewer) at exactly the 0.15 mm DRC minimum | generator table only |
| SWCLK | (14.4, 39.0) → (13.9, 39.5) | 0.50 | Pin escape into the lane above SWDIO; SWDIO's y 38.9 is pinned by J3's shell tabs | — (fan-out) |
| QSPI_IO0 | (25.5, 38.55) → (26.13, 39.18) | 0.63 | Stagger to its via directly over U3.5 | — |
| HSE_OUT | (23.0, 48.0) → (23.7, 47.3) | 0.70 | Part of the fold-back | R8P1-ROUTING-01 |
| CAM_MCU_TX | (32.3, 45.0) → (33.05, 45.75) | 0.75 | U1.42's row to U12.5's row (offset pads) | D56 |

The radio trio's step is the most visible knee on the board. It is forced: a straight trio needs either a 4.15 mm
fence opening, against D16's 2.7 mm limit, or an unstitchable F.Cu GND finger inside the strip.

### 5.2 Fold-backs through vias (cross-layer local bumps)

`viaturn.py` finds 26 vias whose two arms on different layers leave within 45° of each other. One of them, HSE_OUT, is
removable (R8P1-ROUTING-01). None of the 26 is gated.

| Via | Net (class) | Fold | Why it stays |
|---|---|---:|---|
| (11.51, 8.9), (10.41, 8.9) | GNSS_LNA_EN, GNSS_VCC_RF (rfif) | 1.30 / 0.835 | **A2 / A3**, confirmed (§6) |
| (32.6, 71.89 / 74.43 / 76.97 / 79.51) | SERVO1–4_MCU (actuator) | 1.20 each | T-junction: the via feeds the 1 k (B.Cu, x 31.4) and D121; the F.Cu passes over the 1 k after the 10 k pull-down (F.Cu, x 30.4) |
| (8.79, 55.75), (9.5, 55.65) | SPI1_MISO / MOSI (spi) | 1.20 / 0.89 | U4 rotation 0 (axis map, D77); its SPI pads face away from U1; IMU_body_B allows no via (D54) |
| (27.75, 43.83), (17.5, 42.57) | QSPI_IO3 / IO2 (spi) | 1.15 / 0.60 | U3's outer-end via scheme (spike a): the F.Cu crosses the flash and the B.Cu returns along the pad |
| (35.25, 60.5) | RAW_PROTECTED | 1.10 | T between U11.2 and C97.1 (D42 / D46) |
| **(23.7, 46.35)** | **HSE_OUT (crystal)** | **0.95** | **none: removable (R8P1-ROUTING-01)** |
| (40.75, 41.4) | CAM_5V | 0.925 | the sense joins at J9.1's feed via (D41) |
| (35.5, 66.6) | VLOGIC | 0.90 | T for C84.1 (F) and U2.2 / TP83 (B) |
| (13.48, 98.95) | ACT_GATE | 0.87 | Q120.4 (B) under the R121 / TP121 column (F) |
| (34.4, 73.2), (34.4, 69.65) | 3V3 | 0.80 / 0.75 | T to D121.5; In2 tap into the F.Cu hop over SERVO4's B.Cu |
| (0.8, 42.75) | NRST | 0.80 | J2.3 is reachable only from the board edge (D53) |
| (28.4, 88.61), (23.0, 88.33), (11.45, 5.15) | PYRO1_CONT, PYRO1_GATE_N, GNSS_ANT_DC | 0.75 / 0.50 / 0.73 | rigid R7 vias |
| (24.0, 51.1) | NRST | 0.71 | T with C24, 0.65 mm off HSE_OUT's lane |
| (31.75, 47.0) | RAW_ACT_SENSE_MCU | 0.67 | **C5** (R172 under U1's east pad row) |
| (8.72 / 9.97, 62.85) | I2C1_SCL / SDA | 0.58 | T with R12 / R13 |
| (38.25, 33.1) | CAM_FB | 0.30 | T (R72 / R71 / C77) |

### 5.3 Detours and extra vias

- **Two-pad nets over 1.2× and more than 0.8 mm long** (`rg/scan` net_length). Each is inherent or recorded:
  - RADIO_TXEN 2.30×: rigid, D10.
  - CAM_PWR_EN 1.50×: D37's loop round U7.
  - SPI1_SCK 1.56×: D54's forced crossing.
  - The GNSS lanes 1.25–1.33×: the nested river round the USB block.
  - SPI1_MISO 1.26×, QSPI_IO3 1.38×, SPI1_MOSI 1.21×, QSPI_CLK 1.34×: §5.2.
  - RAW_ACT_SENSE_MCU 3.80×: C5.
  - CC2 1.39×: J3.B5 to R8.
- **Vias.** Of the 181 non-GND vias, a signal net carries at most one, except four nets with two:
  - CAM_MCU_RX: D56's inherent RX / TX swap.
  - NRST: the B.Cu run under U1's forward row to J2's edge entry.
  - BAT_ENABLE: across the band and the U9 cluster (D58).
  - ACT_GATE: an F.Cu bar over the 7.7 A B.Cu copper.

  PYRO1_GATE_N and ARM1_SENSE use the rigid exit vias. I found no extra or unneeded via (one-layer vias: 0).
- **Long cross-band lanes.** R122's 0.25 mm RAW_PROTECTED feed (47.1 mm; extra_bends D46 / D69) and BAT_ENABLE
  (47.4 mm, 1.3 mm north of it) cross the band side by side.
  - Both follow from U9 sitting aft of J121 (D36) with Q122 and the switch legs at J1.
  - Each is two to four long orthogonal runs, which is simple, not messy.

### 5.4 Bus tidiness

- **U1 → strip river:** GNSS lanes at 0.6 mm pitch in nested mitred L's; the radio trio at 0.5 mm, MOSI / NSS at 0.6 mm;
  the east-face nest NSS / SCK / DIO1 / NRST at x 31.65 / 32.25 / 32.85 / 33.4.
- **Servo bus:** four F.Cu lanes at 0.5 mm pitch (x 27.5–29.0), straight from U1's forward row to identical 45° turns
  into their rows.
- **Pyro corridor:** three B.Cu lanes at x 18.18 / 18.75 / 19.25, nested at both ends so that nothing crosses.
- **QSPI and IMU:** the QSPI dives under U1 and the IMU fan over U4 / U5, one via per net.
- **USB:** DP / DM flow straight through D4 (USBLC6-2) with no via; the USB-C pairs are joined on F.Cu (DM's loop
  inside J3's pad row, DP's outside), D53.

### 5.5 Pad entries

- **Totals:** 650 pad entries. New copper: 230 outward, 200 lateral, 37 inward, 35 diagonal-out, 8 diagonal-in,
  26 on single pads.
  - The inward exits are the planned dives under U1 (QSPI, HSE, NRST, VCAP, BOOT0, 3V3) and the flow-through D4 entries.
  - The lateral exits on IC pads are corner pads, SOT / WSON pins and the J3 pads (a centroid artefact of my classifier).
- **Pads joined only off-centre:** 48 pads have no track end at their centre.
  - 26 are rigid, or are route_check's recorded `pad_end_offcentre` / `passes_through_pad` information.
  - 12 are deliberate offsets of 0.02–0.075 mm below route_check's 0.1 mm threshold, explained in the generator
    comments: the RAW_ACT_SENSE spine at x 25.92 against pad centres 25.97 (R125, R182, C122); R168.2 (0.03); C77 / R71
    (0.025); C32.1; R163.1; R177.1; R301.1; C97.1.
  - J2's five contacts end 0.10–0.115 mm off centre, outside the TC2030 key-out, deliberately (`r8_route_usb_swd.py`).
- **Pad-edge-only joints:** U9.5, C75.2 and, nearly, U9.7 (0.025 mm deep). None is reported anywhere
  (R8P1-ROUTING-02).

### 5.6 Width, via-size and layer discipline

- **Signals:** every new signal track is 0.2 mm.
  - The actuator gate family (ACT_GATE, ACT_EN, ACT_DRV, BAT_SW_*) and CAM_FB are 0.25 mm.
  - Rigid copper keeps R7's 0.15 mm on RADIO_TXEN and on one PYRO1_CONT piece.
- **Power widths** follow their D-numbers: RAW_PROTECTED 0.5 mm trunk with 0.25–0.4 mm branches (D46); USB_LIMITED
  0.4 mm (D42); VLOGIC 0.5 mm column (D42); 3V3A 0.3 / 0.25 / 0.2 mm (D44).
- **Width steps:** they occur only at pads and junctions (E, 15) and at one pad neck (§4.1).
- **Via sizes:** 0.5 mm on signals and 0.6 mm on power, with five exceptions:
  - SERVO1–4_MCU 0.6 mm;
  - CAM_FB 0.6 mm;
  - BAT_ENABLE mixed (0.6 mm at (16.6, 104.5), 0.5 mm at (40.42, 93.5));
  - the VLOGIC sense via 0.6 mm (R8P1-ROUTING-03);
  - signal-size vias on 3V3, CAM_IO_3V3 and VCAP (D56).
- **Layers:** In1 has no track and In2 only D70's rigid 3.4 mm, as R8_VALIDATION C1 says.
- **Right-angle corners:** 59 new ones mixed with 45° mitres. AGENTS §3 allows them. They cluster at the U1 east-face
  escapes, the SWD / USB entries, the band lanes and the 3V3A / VLOGIC sense Z's, and read as escapes rather than
  carelessness.

## 6. Remaining exceptions: can a DRC-clean edit remove them?

| Item | Result |
|---|---|
| A1 (A8, TP122 via) | Rigid CH1 copper; geometry as recorded (nearest GND via 2.717 mm); not re-probed (D9) |
| A2 / A3 (GNSS limiter vias beyond the pad end) | **Confirmed.** U30.13 / U30.14 span y 9.30–11.10, and U30_KEEPOUT (F.Cu + In1, no non-GND via) starts at y 11.25, so only 0.15 mm is free at the inner end. A 0.5 mm via fits only beyond the aft end (y 8.9) or in the pad. No DRC-clean edit without a via-in-pad |
| C5 RAW_ACT_SENSE_MCU 3.80× | Confirmed forced: R172 sits on B.Cu under U1's east pad row, 0.67 mm from pin 34. The record's "why" cites D33's VLOGIC / RAS crossing, which is the root cause (it puts the RAS lane and R172 under the pin row); the out-and-back via itself is not described. Wording only |
| C9 (D59 polylines) | Each link is one segment group on one layer with no via; seen in the renders |
| E (93 information instances) | Re-counted: equal to the record. Each `u_turn`, `extra_bends` and `short_layer_hop` checked against its D-number (§5) |
| §5.2 fold-backs | HSE_OUT removable (variant `hse`); the rest forced or T-junctions |
| §5.1 knees | the radio trio forced (fence and finger); QSPI_IO3 removable only at the 0.15 mm DRC minimum (judged, not tested) |
| USB_LIMITED–CAM_PWR_EN 0.151 mm | **Not removable.** Variant `gap` (CAM_PWR_EN's run at y 36.65): DRC "pad clearance 1.0000 mm; actual 0.9000 mm" against TP73.1, and check_r8 fails on the same test pad. The run at y 36.8 sits exactly at TP73's 1.0 mm zone |

## 7. Findings

### R8P1-ROUTING-01 (Minor, worth fixing): HSE_OUT folds back through its via; a DRC- and gate-clean redraw removes the fold and shortens the crystal net by 21 %

**Requirement.**
- REQUIREMENTS M2 / AGENTS §3: no needless detours, over the whole board.
- M2's review clause covers what route_check does not test. Its local-bump test follows single-layer chains only.
- Owner priority 2: simple routing.

**Finding** (`qspi_hse` table, `m3_design/r8_route_qspi_hse.py` DIVES; spike (a) RESULT "Crystal Y1"):
- F.Cu: U1.13 (23.0, 52.55) → (23.0, 48.0) → (23.7, 47.3) → via (23.7, 46.35).
- B.Cu: via → (23.7, 47.5) = Y1.3 → (25.33, 47.5) = C26.1.
- The F.Cu runs 1.15 mm north past Y1.3 (B.Cu, pad y 46.8–48.2) to a via beyond the pad's far edge. The B.Cu then comes
  back south 1.15 mm, under the F.Cu, into the pad. For 0.95 mm the two runs lie over each other in plan.
- HSE_OUT is 9.27 mm (7.6 mm from the pin to the crystal pad), against HSE_IN's 4.69 mm.
- The net-level detour test (1.33× its MST) and the single-layer bump audit both pass it. The fold is not in the R8 list,
  and no record says why the via is on the far side.

**Evidence.**
- Variant `hse` (`<s>/e_hse.json`):
  - removes the three F.Cu pieces, the two B.Cu pieces and the via (23.7, 46.35);
  - adds an HSE_OUT via (24.65, 47.5), 0.5 mm, between Y1.3 and C26.1;
  - adds F.Cu (23.0, 52.55) → (23.0, 49.15) → (24.65, 47.5) and B.Cu via → Y1.3 and via → C26.1;
  - adds a GND via (24.65, 46.25), 1.25 mm from the new HSE via.
- Results of the variant:
  - DRC 0 / 0 / 0 with parity; route_check identical to `base` (`rcdiff`: no instance gained or lost); check_r8 OK;
    actuators OK.
  - HSE_OUT 7.36 mm (pin to crystal pad 6.68 mm), two F.Cu segments instead of three, no fold.
  - `tools/reference_audit.py`: 5,525 → 5,180 unreferenced samples (11.57 % → 10.98 %). The Y1_In2_keepout samples fall
    from 1,710 to 1,365.
- Clearances: the new via is 0.10 mm from Y1.3 and 0.13 mm from C26.1, both on its own net. Vias are tented on both sides
  (board setup).

**Why Minor.**
- The electrical effect is negligible: about 0.2 pF less trace capacitance on a CL = 8 pF crystal (Inference).
- The net passes every gated M2 measure.
- It is still the one crystal-net fold that nothing forces, on a net the board otherwise routes tightly.

**Fix.**
- In `r8_route_qspi_hse.py` (DIVES and GND_VIAS), redraw HSE_OUT as in `e_hse.json`. Placing the via at (24.69, 47.5)
  instead gives 0.14 mm to both pads.
- Re-run the step-6 gates and update spike (a)'s figures in M3_R8.

### R8P1-ROUTING-02 (Minor, worth fixing): three untidy entries on large pads, outside route_check's pad test and not in the record

**Requirement.**
- M2: "untidy pad entries … what review checks: … pad-entry tidiness and adjacency on every net".
- R8_VALIDATION E describes `pad_end_offcentre` as "by up to 0.85 mm".

**Finding** (`padedge.py`, `entry.py`):
1. **U9.5 (BAT_IN, the eFuse input).**
   - `r8_power.py:140` draws B.Cu 0.3 mm (41.25, 87.6) → (41.25, 86.7).
   - The end lies exactly on the pad's south edge (pad 0.3 × 2.4 mm, y 84.3–86.7): depth 0.000 mm, 1.20 mm from the
     centre. The joint is made by the track's end cap.
   - Its twin U9.6 (RAW_PROTECTED) starts at its pad centre (D46).
2. **C75.2 (GND).**
   - `r8_power.py:451` CAMERA_GND draws `(41.4, 47.22) → (41.4, 47.8)`.
   - C75 was placed at (40.0, 46.07) (D41), so C75.2's centre is (41.5, 46.07). The stub ends on the pad's south edge
     (depth 0.000) and 0.1 mm off its axis.
   - The other CAMERA_GND entries start at their pad centres, so this one is a stale coordinate (Inference).
3. **C75.1 (CAM_5V).**
   - The 0.8 mm bar from L3.2 runs at x 38.85 against the pad centre 38.5.
   - It overhangs C75.1's inner (body-side) edge (x 39.0) by 0.25 mm. L3.2 and C75.1 overlap by only 0.3 mm in x, so the
     bar has to straddle.

- Also: U9.7 (BAT_DVDT) ends 0.025 mm inside its pad.
- route_check skips all of these: `pad_end_offcentre` tests only pads no larger than 2 mm (route_check.py l. 125).

**Evidence.**
- Variant `pads` (`<s>/e_pads.json`): BAT_IN drawn (41.25, 87.6) → (41.25, 85.5), to the pad centre; the C75.2 stub drawn
  (41.4, 46.07) → (41.4, 47.8).
- Results: DRC 0 / 0 / 0; route_check identical to `base`; check_r8 OK; actuators OK; `padedge.py` leaves only U9.7.
- A first try that moved C75.2's via onto the pad axis at 0.6 mm failed DRC: 0.100 mm to the RAW_PROTECTED trunk at
  x 42.15. That trunk pins the via at x 41.4; a 0.5 mm via on the axis passes.

**Why Minor.** Each joint is continuous copper, DRC-clean and electrically sound: U9.5's track is the pad's own width, so
the copper outline is the same (Inference). It is CAD and entry tidiness, plus an incomplete record.

**Fix.**
- Apply `e_pads.json` in `r8_power.py`.
- For C75.1, either move C75 0.35 mm so that L3.2 and C75.1 share an axis, or record the straddle.
- Let route_check report a track end that lies on a pad's boundary (any pad size), or extend R8_VALIDATION E's text to
  large pads.

### R8P1-ROUTING-03 (Minor): the VLOGIC sense tap uses a power-size via at the DRC minimum from an MCU pin lane, which a signal-size via avoids

**Requirement.** Width and via discipline; robustness. Do not spend clearance next to an MCU pin without need (the R7
P8-ROUTING-02 class).

**Finding** (`gaps.py`):
- The D33 sense via VLOGIC (26.95, 60.5) is 0.6 mm and carries only the R60 divider's µA.
- It sits 0.151 mm (edge to edge) from the SERVO1_MCU F.Cu lane at x 27.5, which runs straight to U1.22.
- VLOGIC is the battery / USB rail (up to the 2S pack voltage), so a short would put that voltage on an MCU pin.

The supply-net copper at the 0.151 mm minimum, for the record:

| Pair | Gap |
|---|---|
| RAW_PROTECTED trunk – GND via (42.15, 49.8) | 0.151 mm |
| RAW_PROTECTED via (35.25, 60.5) – VLOGIC column | 0.151 mm |
| CAM_5V – GND via (40.4, 47.4) | 0.151 mm |
| CAM_IO_3V3 via – CAM_UART_OE | 0.151 mm |
| USB_LIMITED – CAM_PWR_EN (B.Cu, x 28.0–29.95, y 37.25 / 36.8) | 0.151 mm, pinned by TP73's 1.0 mm zone (variant `gap`, §6) |

Others, 0.17–0.18 mm: USB_LIMITED – R172 pads (RAW_ACT_SENSE / _MCU) 0.18; BAT_IN – R81.1 0.18; RAW_PROTECTED – R166
pads 0.176.

**Evidence.** Variant `vlv` (`<s>/e_vlv.json`): the via at 0.5 / 0.3 mm. DRC 0 / 0 / 0; route_check identical; check_r8 OK;
actuators OK. VLOGIC via – SERVO1_MCU 0.200 mm, and to its GND neighbour 0.229 mm (was 0.178).

**Why Minor; not marked worth fixing.**
- Both values pass DRC under tented mask, and JLC's electrical test screens etch shorts (Inference).
- The 0.05 mm gained is real but small.

**Fix.** Make the D33 sense via `VIA_SIG` (0.5 mm) in its generator, and list the 0.151 mm supply–GPIO pair above
(USB_LIMITED / CAM_PWR_EN, forced) in the record.

### R8P1-ROUTING-04 (Minor, worth fixing): cross-layer fold-backs are neither gated nor listed; the deliberate ones on critical nets have no row in the deviation list

**Requirement.**
- M2: every review-only residual is listed with location, measured reason and why it cannot reasonably be removed.
- The gate's local-bump, tiny-jog and fold-back tests follow single-layer chains, so a run that passes its target on one
  layer and returns on the other is left to review.

**Finding** (`viaturn.py`, §5.2): 26 via fold-backs.
- On critical nets the deliberate ones, with no R8_VALIDATION row, are:

  | Net | Via | Fold | Reason recorded only in |
  |---|---|---:|---|
  | QSPI_IO3 | (27.75, 43.83) | 1.15 mm | the generator ("over the flash diagonally") |
  | QSPI_IO2 | (17.5, 42.57) | 0.60 mm | the generator |
  | SPI1_MISO | (8.79, 55.75) | 1.20 mm | D54 |
  | SPI1_MOSI | (9.5, 55.65) | 0.89 mm | D54 |

- **HSE_OUT** is removable (R8P1-ROUTING-01).
- **Already covered:** A2 and A3, C5 (RAW_ACT_SENSE_MCU), and the two rigid CH1 exit vias.
- **Non-critical folds:** the four servo T-vias, ACT_GATE, the NRST edge entry, CAM_5V, VLOGIC, RAW_PROTECTED and 3V3.
  Most are T-junctions; the others are explained in D-numbers.
- The QSPI_IO3 knee of §5.1 (0.5 mm, deliberately 0.65 mm clear of IO1's via) is likewise recorded only in the table.

**Evidence.** `viaturn.py` output (§5.2 table); route_check `INFO` has no category for these.

**Why Minor.** It is a gap in the record, not in the copper: each listed fold has a sound measured reason (§5.2).

**Fix.**
- Add an R8_VALIDATION part C row: "fold-backs through vias", with the four critical-net instances above and their reasons
  (or a route_check information category `via_fold` with the T-junction exemption).
- Optionally, gate the class on critical nets so that a removable one like HSE_OUT fails the build.

## 8. Notes (no finding)

- **IMU / barometer GND lands.** U4.2–U4.3 and U4.6–U4.7 are joined by 0.2 mm tracks running in the 0.15 mm gap between
  adjacent 0.35 mm lands.
  - The mask web over them is 0.10 mm (pad mask margin 0.025 mm). U4.2–3 then has a stub west to the via (7.5, 53.8);
    U4.7 north to (10.5, 52.1). In R7 each of these pads left outward on its own stub.
  - U5.3–U5.4 are joined along y 59.1 inside the MS5611 outline (BARO_body_B allows tracks; the inter-row zone starts at
    y 59.40).
  - Within the encoded rule areas. I could not re-read ST TN0018 (st.com timed out), so I make no claim on it. For the
    DFM reviewer: same-net bridging of adjacent MEMS lands merges their solder.
- **route_check `bump_audit` and pass-through pads.** See §4.2 (BAT_ENABLE through TP84.1 / C87.1). On critical nets this
  is a fail-safe false positive; not a board defect. For the build-integrity reviewer.
- **GNSS_VCC_RF's via (10.41, 8.9)** has its GND via at exactly 1.500 mm, the AGENTS §3 limit (rigid partner).
- **D33's via coordinates are step-4 reservations.** On the board: RAW_ACT_SENSE_MCU (31.75, 47.0) for "(31.9, 47.0)";
  CAM_5V_SENSE (33.3, 46.5) for "(32.55, 46.2)"; V3V3_SENSE (25.9, 54.0) for "(25.75, 54.25)". This is decision history,
  but M3_R8 readers may take them as built.
- **RADIO_NRST's F.Cu lane** (x 33.4, then the 45° run to x 40) passes about 2 mm west of the camera buck's B.Cu switch
  node (CAM_SW, y 37.9) across the board. A layer assignment for the RF and power reviewers, not geometry.

## Appendix: reproduce

```
cd <scratch>/r8p1rt        # r8.kicad_pcb = 429b6db4…; ../p8rt/r7.kicad_pcb = c872a3d3…; proj/ = project copy (kilib symlinked)
PY=<KiCad 10.0.6 python3>
$PY -I inv.py r8.kicad_pcb
$PY -I runscan.py r8.kicad_pcb ../p8rt/r7.kicad_pcb scan_r8.json       # rg/scan.py, R7-rigid attribution
$PY -I r8scan.py r8.kicad_pcb s.json ../p8rt/r7.kicad_pcb               # independent scan
$PY -I entry.py r8.kicad_pcb ../p8rt/r7.kicad_pcb; $PY -I padedge.py r8.kicad_pcb
$PY -I viaturn.py r8.kicad_pcb; $PY -I dent.py r8.kicad_pcb; $PY -I gaps.py r8.kicad_pcb 0.2; $PY -I gndtrk.py r8.kicad_pcb
$PY -I bumps_all.py r8.kicad_pcb                                        # route_check bump_audit on all non-GND nets
./vrun.sh base e_base.json; ./vrun.sh hse e_hse.json; ./vrun.sh pads e_pads.json; ./vrun.sh vlv e_vlv.json; ./vrun.sh gap e_gap.json
python3 rcdiff.py v/base/rc.json v/hse/rc.json
$PY -I <repo>/tools/reference_audit.py v/hse/m3.kicad_pcb --list 0
```
