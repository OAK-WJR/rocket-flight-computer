# R7 pass 2: RF layout and coexistence review

Independent read-only review, 2026-10-15, of `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`03fe75720f46b1382d9d3216dbffd8ae642d0125722c04589ff97c964aa86d54` (checked before and after; unchanged). It covers one
dimension: RF layout and coexistence (REQUIREMENTS F10, plus the RF parts of M1/M2). Vehicle-level choices and
firmware are out of scope.

What was run:
- `tools/check.sh` (temporary copies) gave exit 0: DRC 0, unconnected 0, parity 0, ERC 0, audit, silkscreen, R7
  contract, actuator contract and fit all OK.
- KiCad 10.0.6 `pcbnew` read pads, tracks, vias, courtyards, rule areas and the **filled** zone polygons (point tests
  and polygon distances).
- Copper renders came from a scratch copy cropped to the strip (`kicad-cli pcb export svg`). The board and schematic
  were never saved.
- An independent 2-D finite-difference field solve of the GCPW cross-section; closed-form checks.
- Live JLC template queries (stackup and Dk).
- Maker documents downloaded and read (section 5).

Coordinates: KiCad mm, y = 0 at the aft edge (R7 convention).

## 1. Summary

**No Critical or Major finding in this dimension. Five Minor findings (RF-01 to RF-05).**

The RF strip is built as specified and measures correctly:

- **Stackup.** The KiCad stackup and the Gerber job file equal JLC041611-7628, checked live against JLC's template:
  7628 RC49 % prepreg 0.203 mm with Dk 4.4, core 1.03 mm with Dk 4.38, inner copper 0.030 mm, laminate 1.566 mm.
- **Line impedance.** The drawn line is W 0.300 mm (every RF segment; DRC pins it) with a 0.25 mm gap (fill measured
  0.26–0.28 mm). It solves to **50.3 Ω coated, 52.2 Ω bare** (εeff 3.18) in my own field solve. JLC's engine gives
  50.24 Ω and 52.3 Ω.
- **Launch.** The SMA launch pad, with In1 cut out, is 49–52 Ω.
- **Reference planes.**
  - In1 GND is continuous under every RF track and pad, plus a 0.30 mm margin. The only openings are the two intended
    launch cut-outs (x 11.95–13.75 and 30.64–32.44, y 0–4.6), which are exactly the SMA centre pad plus 0.30 mm.
  - In2 is GND under both cut-outs.
- **Chain order** matches F10 on both chains. Each ESD diode is the first part after its jack. The bias tap is on the
  antenna side of the pi network.
- **Keep-out distances.**
  - Every RF part is ≥ 5.87 mm (courtyard to courtyard) from U2, L1, C5–C9, U7, U8, L3, the buck feedback parts,
    U1, U3 and Y1.
  - Nothing but module escapes and GND sits on F.Cu or In1 under U30.
  - Nothing but GND sits under U31's pad field on any layer.
- **Board-level coupling between the two RF chains is small next to the 39 dB budget** (section 3.11, Inference).
  The ≥ 39 dB figure is set by the off-board antennas and coax and can only be shown on the bench (ORDERING §5 already
  plans S21 J30↔J31 and the keyed C/N0 test).

**Dispositions of the step-B items carried to pass 2 (section 4):**

- **Stitching gaps: accept.**
  - The true continuous gaps are larger than recorded: 4.27 mm on the GNSS west side, not 2.98 mm. RF-03 corrects
    the record.
  - Even so, every gap is ≤ λ/20 in FR4 at 1.61 GHz (4.4 mm) and far below λ/10 at 915 MHz.
  - The return path is the unbroken In1 plane 0.203 mm below the line.
- **The four radio control lines near U30: accept.**
  - Measured to the MAX-F10S body (DS Table 21), not its enlarged courtyard, they are 4.88 mm (DIO1 via, B.Cu side),
    5.04 mm (RXEN), 5.63 mm (NRST) and 5.67 mm (BUSY).
  - They are ≥ 5.9 mm from the GNSS RF copper.
  - They are quasi-static control lines, not clocks, and DIO1/NRST run on B.Cu behind solid In1.
  - The SPI lines are ≥ 6.1 mm from the body.
- **Non-GND copper inside the strip: accept on RF grounds.** The F10 wording needs amending or a recorded waiver
  (RF-04).

## 2. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| RF-01 | Minor | F10 (pi network: shunts not fitted), M2 (paste) | **The four DNP pi-network shunt lands get solder paste.**<ul><li>C303, C305, C313 and C314 are DNP, excluded from the BOM and from position files, but their pads keep F.Paste.</li><li>The released paste Gerber has 0.50 × 0.54 mm apertures on all 8 pads, and ORDERING §4 tells JLC to "use the supplied paste layer exactly".</li><li>Result: bare solder domes on empty 0402 lands with a 0.34 mm pad gap.</li><li>An improbable bridge on one of them would short GNSS_RF_ANT (antenna dark, limiter at ≤ 46 mA), GNSS_RF_IN (receiver deaf) or the radio output (PA into a short).</li></ul> | `fab/m3_gerber.zip` → `m3-F_Paste.gbr`: D03 flashes with aperture D25 (R 0.50 × 0.54) at (11.07, 7.13) and (11.91, 7.13) (C303), (14.65/15.49, 7.13) (C305), (29.76/30.60, 7.6) (C313), (33.34/34.18, 7.6) (C314); Gerber Y = −y. Board pads list F.Mask + F.Paste on each DNP pad. Pad gap 11.32→11.66 = 0.34 mm. | Remove F.Paste from the four DNP lands (footprint pad layers, or have `export_fab.py` drop paste on DNP placeholders) and regenerate the Gerbers. Alternatively, tell JLC to delete those 8 apertures. Inspect the lands on first articles either way. |
| RF-02 | Minor | F10 (ESD at each jack; pi-network footprint), u-blox IM §4.4 (GND stubs ended with a via) | **Parasitics on the RF shunt grounds.**<ul><li>D30.2/D31.2 (ESD), C302.2 (bias-T capacitor) and the DNP shunt GND pads use the house thermal relief (rule "Small GND pad thermal relief": 0.25 mm gap, 0.3 mm spokes).</li><li>Their nearest GND via is 0.75 mm (D30/D31), 0.84 mm (C302), 1.00–1.26 mm (C303/C305/C313/C314) away.</li><li>Each shunt pad also hangs off its series pad by a 0.94 mm stub.</li><li>Inference: about 0.3–0.5 nH (relief) plus about 0.5 nH (stub), roughly 5–10 Ω at 1.575 GHz in series with any shunt later fitted. Negligible while the shunts are DNP (the open stub is about 0.011 λ). It shifts VNA tuning and adds about 10 V to the ESD clamp at 30 A / 0.8 ns.</li></ul> | `m3.kicad_dru` line 91; pad zone connection THERMAL (pcbnew `GetLocalZoneConnection()==1`) on D30.2, D31.2, C302.2, C303.2, C305.2, C313.2, C314.2; nearest vias (14.10, 5.65), (32.79, 5.65), (10.00, 7.00), (14.96, 6.13), (30.69, 6.75), (33.65, 8.45); stubs R304.1→C303.1 (12.85→11.91, y 7.13) etc. | On a respin, give these pads a solid connection (exempt them from the relief rule), put a GND via at each shunt and ESD ground pad, and abut each shunt pad to its series pad. Until then, include these parasitics when tuning on the VNA. |
| RF-03 | Minor | F10 (stitching vias), record accuracy | **The recorded stitching gaps understate the real ones.**<ul><li>stepB_handoff §3/§4 item 4, M3_R7 §"R7 board" and R7_VALIDATION give "three gaps of 2.17–2.98 mm". That is measured per net segment, treating the GNSS_RF_ANT/GNSS_RF_IN boundary at R304 (and R316) as a "line end".</li><li>The continuous via-to-via gaps are larger: GNSS west **4.27 mm**, (11.60, 4.15) → (12.61, 8.30), 4.76 mm along the path; radio west **3.68 mm** via to via, (30.69, 6.75) → (31.13, 10.40), about 1.55 mm to U31.7's GND pad edge.</li><li>The gaps are acceptable (section 3.6); only the record is wrong.</li></ul> | pcbnew GND vias within 2 mm of each line centre, ordered along the path (section 3.6 table). | Correct the three documents to the values in section 3.6, marked as accepted with the λ/20 reasoning. No copper change. |
| RF-04 | Minor | F10 ("every copper layer GND outside the module pads and RF lines") | **The requirement text is not met literally, though acceptable on RF grounds.** Non-GND copper in the strip (y < 23.5) besides module pads and RF lines:<ul><li>B.Cu: the limiter nets under U30 (GNSS_VCC_RF/LNA_EN/ANT_SRC/GATE/PD/DC), the RADIO_TXEN loop (x 24.5, y 7.8–20.15), RADIO_DIO1 (x 32.4, y 20.15–23.7) and the RADIO_NSS hop (23.2–23.6, 15.3–17.3).</li><li>F.Cu: the radio SPI and control lanes between the modules (x 20.6–23.2, y 9–23.3), RADIO_NRST along x 40 (y 14–24.5), 3V3_RADIO along y 21.6 (x 24.2–35.1), 3V3 to FB31 along x 35.1, GNSS escapes and SAFEBOOT_N (y 10.2, x 2–6).</li><li>RF-wise this is fine: In1 is solid under all of it, In1/In2 carry only GND in the strip (check_r7), nothing but GND crosses U31's pad field, and the u-blox rule (top two layers) is met under U30.</li></ul> | pcbnew track/via dump y < 23.5; `tools/check_r7.py` STRIP_F/STRIP_B/STRIP_VIA (lines 67–73). | Amend F10 to name the allowed copper, for example "…GND outside the module pads, the RF lines, and each module's own supply and interface traces; the antenna-bias limiter may sit on B.Cu under the GNSS module". Or record the waiver in M3_R7 and R7_VALIDATION. |
| RF-05 | Minor | F10 (keep-outs, stitching) | **RF geometry is only partly regression-checked.**<ul><li>DRC pins W/gap and the keep-out custom rules, and check_r7 pins the strip's net/layer lists and the launch cut-outs.</li><li>Nothing checks fence pitch, stitching pitch beside the lines, or In1 continuity under the RF copper.</li><li>`U31_KEEPOUT` (25.66–34.06 × 9.80–18.20) covers only the area between the pad rows, while the module body is 24.86–34.86 × 9.0–19.0. STRIP_B allows RADIO_TXEN/DIO1/NSS on B.Cu anywhere in the strip, so a later B.Cu route under U31's pad bands would pass both DRC and check_r7 (EBYTE §4.1 forbids wiring under the module).</li><li>Today's copper is clean (section 3.7).</li></ul> | `m3.kicad_dru` lines 15–42; board rule area `U31_KEEPOUT` (m3.kicad_pcb ~l. 96628); `check_r7.py` lines 66–74, 400–443. | Grow `U31_KEEPOUT` to the module body (24.86–34.86 × 9.0–19.0) on B.Cu/In2. Add to check_r7: GND-via pitch ≤ 2 mm along the fence except the two named openings; In1 GND under RF copper +0.3 mm except the launch cut-outs; a stitching-gap ceiling (for example 4.5 mm). |

No Critical or Major findings. No serious defect outside this dimension was tripped over.

## 3. Measurements

### 3.1 Stackup (KiCad, job file, JLC)

| Layer | KiCad / `m3-job.gbrjob` | JLC041611-7628 (live, 2026-10-15) |
|---|---|---|
| F.Cu | 0.035 | 0.035 (1 oz) |
| Prepreg | 0.203, εr 4.4, tanδ 0.02 | 7628×1 RC49 % 8.6 mil, 0.203 mm, Dk 4.4, NP-155F |
| In1 | 0.030 | 0.030 |
| Core | 1.03, εr 4.38 | "1.1 mm 1/1 oz with copper", 1.03 mm, Dk 4.38, NP-155F |
| In2 | 0.030 | 0.030 |
| Prepreg | 0.203, εr 4.4 | 0.203, Dk 4.4 |
| B.Cu | 0.035 | 0.035 |
| Total | 1.566 + mask | compressionThickness 1.566 |

- Both match. The job file has revision M3-ASSY-R7, 46.1 × 118.1 mm, 4 layers, 1.6 mm and ENIG.
- ORDERING §3 names JLC041611-7628 explicitly.

### 3.2 GCPW impedance for the drawn geometry

The drawn line is F.Cu W 0.300, gap 0.25 mm (DRC rules "R7 RF50 line width/coplanar gap"), over In1 GND at
0.203 mm, t 0.035 mm.

| Method | Coated (mask εr 3.8, 0.025 mm on laminate, 0.015 mm on copper) | Bare |
|---|---|---|
| This review: 2-D finite-difference quasi-static solve (half-domain, about 10 k nodes, converged to 1e-8) | **50.3 Ω, εeff 3.18** | **52.2 Ω, εeff 2.95** |
| JLC impedance engine (pass1_layout §5.2) | 50.24 Ω, εeff 3.19 | 52.3 Ω |
| Closed form, Ghione CB-CPW (zero thickness / Gupta thickness on both k / Qucs-KiCad thickness model) | — | 56.9 / 48.1 / 55.3 Ω (the bracket; closed forms are poor at t/S = 0.14) |

Further results:
- Gap as filled, 0.26–0.28 mm: +0.3…+0.8 Ω (closed-form sensitivity).
- The FD solver checks out against itself: at t = 0.004 mm it gives 55.3 Ω against the analytic thin-strip 56.9 Ω.
- SMA launch pad (W 1.2, gap 0.30, In1 removed, so referenced to In2 at 1.263 mm): FD 49.0 Ω coated (JLC 51.7 Ω).
  Without the cut-out it would be 21–23 Ω.
- 0402 pads on the line (W ≈ 0.54): about 35–39 Ω over 0.5–0.6 mm, about 0.005 λ at L1.

### 3.3 Drawn RF paths

| Chain | Path (centre coordinates) | Lengths |
|---|---|---|
| GNSS | J30.5 pad (12.25–13.45, 0.2–4.4) → track x 12.85 north → D30.1 (12.85, 5.2) → L30.2 (12.85, 6.18) → R304.1 (12.85, 7.13), with the C303.1 stub west to 11.91 → R304 across x → R304.2 (13.71, 7.13), with the C305.1 stub east to 14.65 → track x 13.71 north → U30.11 RF_IN pad (13.31–14.11, 9.3–11.1) | Track 4.83 + 3.07 mm. Pad end to module pad edge 5.76 mm. Jack pad centre to module pad edge 7.86 mm, about 0.074 λg at L1 (λg 107 mm) |
| Radio | J31.5 pad (30.94–32.14, 0.2–4.4) → x 31.54 north → D31.1 (31.54, 5.2) → R316.1 (31.54, 7.6), with the C313.1 stub west to 30.60 → R316.2 (32.40, 7.6), with the C314.1 stub east to 33.34 → x 32.40 north → U31.6 ANT pad (31.95–32.85, 8.3–9.8) | Track 5.30 + 1.45 mm. Pad end to module pad edge 4.76 mm. Pad centre to pad edge 6.86 mm, about 0.037 λg at 915 MHz |

Separation between the chains:
- Jack axes 18.69 mm apart (F10 ≥ 12 mm).
- U30.11 to U31.6: 18.73 mm.
- Nearest GNSS RF copper to nearest radio RF copper: 15.45 mm.
- U30 to U31 courtyards: 7.66 mm.

### 3.4 Reference planes

- **In1 under the RF copper.** The filled GND_In1 polygons were point-tested at 0.05 mm spacing over every RF-net
  track and pad dilated by 0.30 mm.
  - Missing points fall only inside the two intended launch cut-outs.
  - There is one other hole: the GNSS_ANT_DC via's own antipad at (11.45, 5.15), which sits on L30's DC side.
  - Along the line centres, In1 is present at ±0.15/0.4/0.6/0.8 mm everywhere past y 4.6.
- **Launch cut-outs.** Rule areas `R7_J30_launch_In1` (11.95–13.75, 0–4.6) and `R7_J31_launch_In1`
  (30.64–32.44, 0–4.6): pour keep-out on In1 only.
  - In1 is absent across x 11.95–13.70 at y 2.3 and present from 11.90 and 13.75 outward.
  - F.Cu GND starts 0.30–0.35 mm from the 1.2 mm pad.
- **In2 and B.Cu.** Both are GND under the whole launch pad from y 0.5 (board edge clearance), and continuous under
  both lines (0 missing points).
- **Signal-via antipads** on In1/In2 measure 0.51–0.56 mm radius. None reaches the RF keep-in region.
- **GND coverage of the strip** (y 0.6–23.4): F.Cu 76.7 %, B.Cu 92.0 %, In1 95.1 %, In2 96.6 %.

### 3.5 Launch geometry (Kinghelm KH-SMA-KE8-G drawing, 2019-08-10)

- **Pads against the jack.**
  - Centre pad: 1.2 × 4.2 mm, from y 0.2 to 4.4. The pin is Ø0.95 and 4 mm long.
  - Ground legs: 1.2 × 4.2 mm at x ±2.55, on F.Cu (pads 1 and 2) and B.Cu (pads 3 and 4). The drawing gives
    0.9 mm square legs with 4.2 mm inner and 6.0 mm outer spacing.
- **Track entry.** The track starts at the pad centre and steps straight from 1.2 to 0.30 mm at y 4.4, with no taper.
  Both sides of the step are about 50 Ω, so no taper is needed. The 0.2 mm of line between the pad end and the end of
  the In1 cut-out (y 4.4–4.6) is about 70 Ω, which is negligible.
- **Stitching vias at each jack.** Each jack has 8 vias, at x ±1.45 from the axis (y 1.0, 2.3, 3.6) and ±1.25
  (y 4.15).
  - They sit between the legs and the centre pad.
  - They are 0.35–0.55 mm from the centre pad edge and 0.2 mm from the leg pads.
  - They are tented on both sides by board default.
- **Leg pads** have a solid connection to the pours: SMD pads on GND_F/GND_B, padconn THT_THERMAL.

### 3.6 Stitching beside the lines and the strip fence

GND vias within 2.0 mm of the line centre on each side, in path order (0.6 / 0.3 mm vias):

| Side | Vias (x, y) and lateral distance | Largest via-to-via gap |
|---|---|---|
| GNSS west | (11.4, 1.0/2.3/3.6) 1.45, (11.60, 4.15) 1.27, then (12.61, 8.30) 1.10, (12.86, 8.83) 0.85 | **4.27 mm** ((11.60, 4.15) → (12.61, 8.30)); L30, C302, C303 and the ANT_DC via fill this stretch |
| GNSS east | (14.3, 1.0/2.3/3.6), (14.10, 4.15), (14.10, 5.65) 1.25, (14.96, 6.13) 1.60, (14.81, 8.30) 1.10, (14.56, 8.83) 0.85 | 2.18 mm |
| Radio west | (30.09, 1.0/2.3/3.6), (30.29, 4.15), (30.69, 5.65) 0.85, (30.69, 6.75) 0.85, then U31.7 GND pad (edge y 8.3) and its via (31.13, 10.40) | 3.68 mm via to via; about 1.55 mm to the U31.7 pad |
| Radio east | (32.99, 1.0/2.3/3.6), (32.79, 4.15), (32.79, 5.65) 1.25, (32.39, 6.75) 0.85, (33.65, 6.60) 1.60, (33.65, 8.45) 1.26 | 2.06 mm |

**Judgement on the step-B gaps: accept** at 1.18–1.61 GHz and at 915 MHz.
- **Gap against wavelength.** λ in FR4 (εr 4.4) is 89 mm at 1.61 GHz and 156 mm at 915 MHz, and λg in the line
  (εeff 3.18) is 105 and 184 mm. The worst gap, 4.27 mm, is λ_FR4/21 (λg/24) at 1.61 GHz and λ_FR4/37 at 915 MHz,
  within the usual λ/20 fence rule at the highest GNSS frequency. Inference: practice rule, not a maker figure.
- **No resonance.** The unstitched coplanar fragments are < 3 mm long, ≪ λg/4 (about 26 mm at L1). No slot or stub
  resonance is possible.
- **Return path.** The GCPW return current flows mainly in In1, 0.203 mm below, which is verified continuous
  (section 3.4). Losing a side ground for about 2 mm lifts the local impedance by only a few ohms (microstrip limit,
  Inference).
- **Lines are short.** They are ≤ 0.074 λg long, and the cascade estimate in section 3.12 gives RL ≥ 19 dB.
- **No room for more vias.** No via fits beside L30/C302/C303 without moving parts (ViaCheck, as step B reports);
  adding one would buy nothing measurable.

**Fence** at y 23.3: 21 GND vias at x 0.9, 2.9, 4.9, 6.3 | 12.4, 14.2, 16.2, 18.2, 20.0 | 23.8, 25.8 … 37.8,
39.4, 41.4, 43.4, 45.1.
- Pitch 1.4–2.0 mm. Two openings: **6.1 mm** (x 6.3–12.4: GNSS escapes, 3V3_GNSS) and **3.8 mm** (x 20.0–23.8: radio
  lanes).
- Other crossings pass between vias at 2.0 mm pitch: GNSS_RESET_N F.Cu x 14.81, RADIO_DIO1 B.Cu x 32.4, 3V3 F.Cu
  x 35.1, RADIO_NRST F.Cu x 40.0.
- **Accept.**
  - The openings are λ_FR4/15 at 1.61 GHz (6.1 mm). Inference: their half-wave aperture resonance lies near 12 GHz.
  - In1 is one continuous GND plane under the whole board, so the fence stitches layers rather than isolating anything.
  - It does not separate GNSS from radio: both sit inside the strip, which has a 2 mm staggered lattice (187 GND vias
    at y < 23.6).
  - The largest F.Cu/B.Cu GND regions without a via within 3 mm are small, edge-connected fingers: (23.85, 10.85)
    between the SPI lanes and U31's west pads; (9.6, 20.85) among U30's forward escapes; and the left edge
    x 0.3–2.05, y 10.75–22.65, where the TP30 legend window removed lattice vias. All are ≤ 4 mm from a via, far below
    λ/4.

### 3.7 Copper inside the strip and under the modules

- **In1 and In2** carry GND only in the strip (check_r7 enforces it; confirmed).
- **Under U30's body** (5.36–15.46 × 10.10–19.80, DS Table 21 nominal 10.1 × 9.7, centred on U30):
  - F.Cu: only U30's own pad escapes, all running outward, and the GND pour.
  - In1: GND only.
  - 11 tented GND vias.
  - B.Cu: the limiter nets. This is allowed: u-blox IM §4.4 restricts only the top two layers.
- **Under U31's body** (24.86–34.86 × 9.0–19.0):
  - Only U31's own escapes, all running outward.
  - RADIO_RXEN runs along y 9.05 from pad 10 west, overlapping the body's aft edge by 0.1–0.2 mm. It is a static
    enable.
  - 16 tented GND vias.
  - Nothing non-GND inside `U31_KEEPOUT` on any layer.
  - The TXEN B.Cu loop passes outside the body: x 24.5, about 0.3 mm outside; y 7.8 and y 20.15.
- **Vias** are tented on both sides by board default (`m_TentViasFront/Back = True`).

### 3.8 Chain order, ESD placement, bias tee and limiter

- **Order.**
  - GNSS: J30 → D30 → L30 bias tap (C302 at its cold end) → C303 shunt (DNP) → R304 0 Ω → C305 shunt (DNP) → RF_IN.
  - Radio: J31 → D31 → C313 (DNP) → R316 0 Ω → C314 (DNP) → ANT.
  - Both chains match F10, M3_R7 and pass1_electrical §6.
- **ESD.**
  - D30.1 and D31.1 sit on the line 0.8 mm past the jack pad end, outside the In1 cut-out. Each GND pad is on the far
    side of the line, 0.75 mm from a GND via (relief: RF-02).
  - ESD103-B1-02: CL 0.09 pF typical at 1 GHz, 0.2 pF maximum at 1 MHz; VRWM ±15 V (Infineon DS rev 1.3, features
    and Table 3). The board estimate is |Γ| ≈ 0.05 at 1.6 GHz, negligible.
  - The radio's +22.3 dBm peak, about 4.1 V, rising to about 7.5 V at 10:1 VSWR, stays below VRWM.
- **Bias tee.**
  - L30 pad 2 is on the line at y 6.18, with the body across x and no stub. C302 (10 nF, u-blox C14) is 0.92 mm away
    at the cold end.
  - The GNSS_ANT_DC via (11.45, 5.15) takes the feed to B.Cu, under the RF line at x 13.55. In1 and In2 GND lie
    between them.
  - The DC route Q30.D → L30 is about 10.5 mm long. VCC_RF leaves U30.14 through a via at (10.41, 8.30), 1.45 mm from
    the RF copper.
  - LNA_EN's via (11.51, 8.30) is 0.79 mm from the C303 stub. Its In1 antipad edge is at y 7.74, clear of the stub's
    gap region, which ends at y 7.53.
- **Limiter.** Q30, Q31, Q32 and R300–R303 form a compact block on B.Cu inside x 3.3–12.5, y 9.5–18.9, under U30's
  west half. Loop stability is the electrical reviewer's item and stays a bench item (M3_R7). Placement-wise there is
  no RF exposure: it is all DC on B.Cu behind two GND planes.

### 3.9 Keep-out distances (courtyard to courtyard, pcbnew)

| RF part | Nearest restricted part | Distance |
|---|---|---|
| FB30 | C6 (logic-buck input) | 5.87 mm |
| C301 | C6 | 6.99 mm |
| U30 | C6 | 7.19 mm (U2 9.66, L1 10.90, U3 10.32, U1 23.56, Y1 31.24, U8 75.1, L3 78.5) |
| C300 | C6 | 7.20 mm |
| U31 | C6 | 9.09 mm (U2 11.97, L1 10.91, U3 11.26, U1 25.06, Y1 31.96, U8 72.9, L3 76.8) |
| FB31 | U3 | 9.90 mm |
| Every other RF part (chain, limiter, decoupling) | C6 / U3 | 10.8–24.9 mm |

The restricted set was U2, L1, C5–C9, U7, U8, L3, C72–C77, R71, R72, TP71, U1, U3 and Y1: every part on SW_NODE, BST,
CAM_SW, CAM_BST or CAM_FB, plus the bucks' input and output capacitors. Net-copper scan: no SW_NODE, BST, QSPI, SPI1,
SWD or USB copper within 8 mm of U30, U31 or either RF track. **F10's 5 mm is met with margin.**

### 3.10 Radio interface lines near U30 (step-B exception list)

Distances are to the MAX-F10S body (DS Table 21), to the body plus its 0.6 mm de-paneling tab, and to the GNSS RF
copper:

| Net | Layer at the closest point | Body | Body + tab | GNSS RF copper | Activity |
|---|---|---|---|---|---|
| RADIO_DIO1 | via (18.4, 24.0), B.Cu run y 24.0 | 4.88 | 4.56 | 13.3 | one edge per radio IRQ |
| RADIO_RXEN | F.Cu x 20.6 | 5.04 | 4.44 | 5.92 | changes only on RX/TX mode change |
| RADIO_NRST | via (19.0, 24.5), B.Cu run y 24.5 | 5.63 | 5.29 | 14.0 | static after boot |
| RADIO_BUSY | F.Cu x 21.2 | 5.67 | 5.07 | 7.05 | a few edges per SPI command |
| RADIO_MISO_MCU / MOSI / SCK / NSS | F.Cu x 21.6 / 22.0 / 22.4 / 23.2 | 6.07 / 6.47 / 6.87 / 7.49 | 5.47–6.89 | 7.66–10.1 | SPI bursts, ≤ 16 MHz |

**Judgement: low coexistence risk; accept.**
- None of the four lines is a clock or carries continuous periodic energy. Their edges are rare and aperiodic.
- DIO1 and NRST run on B.Cu behind continuous In1 GND.
- BUSY and RXEN run on F.Cu over In1 at ≥ 5 mm from the shielded module body. U30's RF input is at the module's
  opposite (aft-east) corner, ≥ 5.9 mm away, behind the GND-flanked GCPW.
- The highest-energy aggressors are the SPI lines, which are ≥ 6.1 mm from the body and ≥ 7.7 mm from the RF copper.
- Step B measured to U30's courtyard, which adds the 12.5 mm T-paste span and the tab (about 1.1–1.5 mm per side), so
  its 3.2–4.7 mm figures are conservative.
- Bench confirmation is already planned: keyed C/N0 test, and u-center UBX-MON-SPAN while the radio and SPI are
  active.

### 3.11 Radio-to-GPS isolation: what the CAD can show (F10 ≥ 39 dB)

The budget: +22.3 dBm maximum (EBYTE manual §2.2) against −17 dBm MAX-M10S immunity at 915 MHz (M10S IM R05
Table 43), so ≥ 39.3 dB. MAX-F10S immunity is "currently not available" (F10S IM §4.3.2), and RF_IN is rated 0 dBm
absolute maximum (F10S DS Table 12). u-blox states that interference "is typically first coupled into the antenna"
(IM §4.3.3). The antennas are off-board, so the budget is set by the antennas, their coax and the bay layout, and is
Bench-verified.

Board-level paths, as far as the CAD goes:

1. **Trace to trace and jack to jack.**
   - Two fenced GCPWs, with the nearest RF copper 15.45 mm apart (about 76 × the 0.203 mm dielectric height).
   - Solid GND on four layers between them, the 2 mm lattice, and shielded SMA bodies 18.69 mm apart.
   - Inference: coupling well below −60 dB.
2. **Module to module.**
   - Courtyards 7.66 mm apart; the RF pins 18.73 mm apart, on far corners.
   - The MAX-F10S has a SAW–LNA–SAW front end (IM §4.3) under RF shields (IM §5, "Conformal coating", p. 72). The E22
     module's shielding is not documented in its manual (Inference).
3. **Supply.**
   - Separate ferrites: FB31 feeds the radio with C311 100 nF, C312 10 nF and C310 22 µF, whose pads are 1.8, 2.0
     and 3.6 mm from U31.1. FB30 feeds the GNSS with C300 10 µF and C301 100 nF.
   - They share only the 3V3 plane and U2. Radio TX current reaches the GNSS VCC only as a slow load step (RampTime
     ≥ 200 µs per pass1 §5.4), not at RF.
   - BLM18KG impedance above 100 MHz is not in the Murata spec sheet read here (Inference: ≥ 100 Ω at 915 MHz).
   - Supply RF never reaches RF_IN directly.
4. **Ground.** Common-impedance coupling across a four-layer solid GND at 915 MHz is negligible (Inference).
5. **Control lines.** RXEN and TXEN leave U31 beside its RF corner. RXEN runs past U30 at ≥ 5.9 mm from the GNSS RF
   copper, with no gain path into RF_IN (Inference: negligible).

**Conclusion.** No board-level path is expected to use a meaningful share of the 39 dB budget (Inference). The board
cannot show the requirement, and the requirement does not depend on the board. ORDERING §5 has the right evidence:
- VNA S21 J30↔J31 at 915/1176/1575 MHz (target ≤ −50 dB) bounds the board's share;
- the keyed-transmitter C/N0 test with flight antennas shows the system figure.

### 3.12 Board-only return-loss estimate (Inference)

A lossless cascade of the drawn sections:
- launch 49 Ω × 4.2 mm, then 0.2 mm at about 70 Ω;
- 0.30 mm line at 50.3 Ω;
- the D30/D31 pad with 0.2 pF;
- the L30 pad with a ≥ 500 Ω choke;
- the DNP stubs as open lines of 1.2 mm;
- R304/R316 as 0.4 nH (assumed).

Result:
- GNSS: |S11| ≈ 0.09–0.11 (RL ≈ 19–21 dB) at 1.176–1.61 GHz, mismatch loss ≤ 0.05 dB;
- radio: |S11| ≈ 0.055 (RL ≈ 25 dB) at 915 MHz, mismatch loss ≈ 0.01 dB.

The board geometry is not the limiting factor; the jack, the module ports and the antennas are.

## 4. Dispositions of the items carried to pass 2 (R7_VALIDATION, "Carried to pass 2")

| Item | Disposition |
|---|---|
| Three stitching gaps "2.17–2.98 mm" | **Accept.** The true continuous gaps are 4.27 / 3.68 / 2.18 mm (section 3.6), all ≤ λ/20 at 1.61 GHz in FR4, with In1 verified continuous. Correct the record (RF-03). |
| Four radio control lines 3.2–4.7 mm from U30's courtyard | **Accept.** They are 4.88–5.67 mm from the module body and ≥ 5.9 mm from the GNSS RF copper. They are quasi-static, not F10 "fast digital lines", and DIO1/NRST sit behind In1 (section 3.10). |
| RXEN/TXEN beside U31's own RF stub (2.77 / 1.56 mm to RADIO_RF copper) | **Accept.** They are the module's own RF-switch pins, inherent to the EBYTE pinout, and static during TX/RX. |
| Radio signals and the limiter on B.Cu inside the strip | **Accept on RF grounds**; amend F10's wording or record a waiver (RF-04). |

## 5. Sources

- u-blox MAX-F10S integration manual UBXDOC-963802114-12892 R01:
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_IntegrationManual_UBXDOC-963802114-12892.pdf
  - §4.1.1 (VCC series resistance ≤ 0.2 Ω), p. 60;
  - §4.3 (SAW–LNA–SAW front end, built-in DC block), §4.3.2 ("out-of-band immunity data are currently not
    available"), §4.3.3 (coupling is first into the antenna; S21 test), p. 64–65;
  - §4.3.4 (L4 bias inductor > 500 Ω at L1/L5; C14), p. 65–66;
  - §5 "Conformal coating" (the module has RF shields), p. 72;
  - §4.4 (keep at least 5 mm to any RF component; GND vias; "any stubs at the ground planes must be avoided or ended
    with a via"; ground the top and second layer under the module, with no signal lines there; CPW with ground on the
    second layer; RF line 50 Ω, as short as possible, ground filled with GND vias), p. 66–67;
  - Table 40 (C14 10 nF), Table 42 (L4 LQG15HS47NJ02).
- u-blox MAX-F10S data sheet UBXDOC-963802114-12732 R03:
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_DataSheet_UBXDOC-963802114-12732.pdf
  - Table 12 (Prfin 0 dBm absolute maximum; ±5.5 V DC at RF_IN; ICC_RF 200 mA);
  - Table 13 (VCC_RF = VCC − 0.1 V, 50 mA; Zin 50 Ω);
  - Table 21 (A 10.1, B 9.7 nominal; tab).
- u-blox MAX-M10S integration manual UBX-20053088 R05:
  https://content.u-blox.com/sites/default/files/MAX-M10S_IntegrationManual_UBX-20053088.pdf
  - Table 43, p. 79: −17 dBm immunity at 915 MHz, low-gain mode.
- EBYTE E22-900MM22S user manual (via LCSC):
  https://datasheet.lcsc.com/datasheet/pdf/70331b0eaf0eedaea0129e9e66d9a011.pdf?productCode=C5333985
  - §2.1 (blocking 10 dBm, VCC ≤ 3.7 V); §2.2 (maximum TX power 22.3 dBm);
  - §3 (ANT stamp hole, about 50 Ω);
  - §4.1 p. 5 (no high-frequency digital, analog or power routing under the module; keep away from interference
    sources).
- Kinghelm KH-SMA-KE8-G drawing (2019-08-10):
  https://datasheet.lcsc.com/datasheet/pdf/35ad22a9bea57e53d493009a20c931ef.pdf?productCode=C530661
  - 50 Ω, DC–6 GHz, VSWR ≤ 1.35; pin Ø0.95; legs 0.9 mm at 4.2 / 6.0 mm; pin 4 mm.
- Infineon ESD103-B1-02 series, rev 1.3:
  https://datasheet.lcsc.com/datasheet/pdf/9f837311bec7e3ead15a9d62fb0575b0.pdf?productCode=C535146
  - CL 0.09 pF typical at 1 GHz; 0.13 / 0.2 pF typical / maximum at 1 MHz; VRWM ±15 V.
- Murata BLM18KG spec:
  https://datasheet.lcsc.com/datasheet/pdf/2d503a4b167da9bb5d0eb4a3fa711314.pdf?productCode=C88980
  - Gives impedance at 100 MHz only.
- JLC stackup template (live, 2026-10-15):
  - POST https://cart.jlcpcb.com/api/overseas-shop-cart/v1/shoppingCart/getImpedanceTemplateSettings with
    `{"cuprumThickness":1,"insideCuprumThickness":1,"stencilLayer":4,"stencilPly":1.6}` returns "No requirement" =
    JLC041611-7628 (thicknesses above).
  - POST https://jlcpcb.com/api/jlcTools/impedance/selectPageImpedanceDefaultTemplate (4 layers, 1.6 mm, 1 oz inner)
    returns JLC041611-7628 with Dk 4.4 (7628 RC49 %, NP-155F) and core Dk 4.38.
- Project:
  - `docs/REQUIREMENTS.md` F10/M1/M2; `docs/M3_R7.md`; `docs/ORDERING.md` §3–5; `docs/R7_VALIDATION.md`;
  - `stepB_handoff.md`; `pass1_layout.md` §5; `pass1_electrical.md` §6;
  - `m3.kicad_dru` lines 15–42 and 91; `tools/check_r7.py` lines 66–74 and 400–443;
  - `fab/m3_gerber.zip` (`m3-F_Paste.gbr`, `m3-job.gbrjob`).

## 6. Inferences (not measured, or not from a primary source)

- **Stitching rules.** The λ/20 fence-pitch rule and the "fragments ≪ λg/4" argument are engineering practice, not
  maker figures.
- **Coupling figures.** The board-level coupling estimates (< −60 dB trace to trace; supply and ground paths
  negligible) are not computed with a 3-D solver. The S21 J30↔J31 bench measurement is the evidence.
- **Parasitics.** The thermal-relief and stub inductances (about 0.3–0.5 nH and about 0.5 nH) and the resulting ESD
  clamp increment are estimates.
- **Cascade estimate.** The return-loss cascade in section 3.12 uses assumed parasitics (R304/R316 0.4 nH, end
  capacitance 0.03 pF, L30 ≥ 500 Ω per u-blox).
- **Field solve.** It is quasi-static 2-D with a rectangular conductor and an approximate conformal mask. JLC's
  engine, which uses a trapezoidal conductor, agrees within 0.1 Ω.
- **Supply and modules.** The BLM18KG impedance at 915 MHz and the E22 module's shielding are not documented in the
  sources read.
- **Fence apertures.** The aperture-resonance frequency is a half-wave estimate.

## 7. Method (reproduction)

All scripts ran under KiCad's Python on a copy of the board in a scratch directory. They are not in the repository.

- **Fill tests.** Build a `SHAPE_POLY_SET` from `zone.GetFilledPolysList(layer)` of every GND zone per layer, then
  `Contains(VECTOR2I)` at 0.05 mm steps (In1 under RF copper dilated by `TransformShapeToPolygon(…, 0.30 mm)`).
- **Distances.** Bisection on `SHAPE_POLY_SET.Collide(shape, clearance)` between courtyards (`GetCourtyard`), body
  rectangles and `GetEffectiveShape` of tracks and vias.
- **Stitching.** GND vias within 2 mm of each line's centre path, split by side (sign of the cross product), ordered by
  path coordinate; via-to-via Euclidean gaps.
- **Paste.** Parse `m3-F_Paste.gbr`, take the D03 flashes and their aperture (D25 R 0.50 × 0.54), and match them to
  the DNP pad centres (Gerber Y = −y).
- **Impedance.** 2-D finite volume, symmetric half-domain, grounded lid at 3 mm, SOR to 1e-8. Z0 = 1/(c√(C·C0)) from
  field energy, with and without dielectric.
- **Gate.** `tools/check.sh` exit 0. Board SHA-256 unchanged after the review.
