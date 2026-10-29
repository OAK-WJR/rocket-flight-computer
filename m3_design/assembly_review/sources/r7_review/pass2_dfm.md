# R7 pass 2: DFM, assembly and fabrication package (independent review)

Read-only review, 2026-10-15 (local; live JLC data 2026-10-16 05:48Z), of the uncommitted R7 worktree
(`m3-assy-r7`, base `3b215ba`). Board `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`03fe75720f46b1382d9d3216dbffd8ae642d0125722c04589ff97c964aa86d54` (checked before and after; unchanged).
Scope: footprints against maker drawings and JLC/EasyEDA lands, courtyards, mask, paste, MSL and reflow, the
jack overhang and JLC's through-hole step, rails and tab windows, tooling holes, silkscreen rules, the
regenerated fab package, procurement and cost. Coordinates are KiCad mm (y = 0 aft edge); Gerber Y = −y.

## 1. Summary

The R7 manufacturing package is in good shape. Every new footprint matches its maker drawing; the lands
match JLC/EasyEDA by pad number; the fab package regenerates byte-identical (apart from timestamps) from the
board; the manifest binds it; the CPL check passes; live JLC stock covers every line except the documented
U4 consignment; and M3 is met at $110.93 per board with 52 extended codes. `tools/check.sh` passes at zero
(rerun here).

One **Major** finding: R100 pad 1 (bottom, soldered 0603) has an open via hole in its pad opening, which
breaks REQUIREMENTS M2. It came over from R6, and neither the gate nor ORDERING catches it. The other ten
findings are **Minor**: DNP pads carrying paste, the unsupported forward end (the forward short edge has
compliant tab windows that ORDERING does not use), hand-soldering exposure at the SMA jacks, U30 T-paste
over vias, and a few documentation items. One of these closes an open item: the LS120 reflow rating is now
read from the maker's figure.

Findings: Critical 0, Major 1 (DFM-01), Minor 10 (DFM-02 … DFM-11).

## 2. Findings

| ID | Sev. | Req. | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| DFM-01 | Major | M2 ("No via holes open into soldered SMD pads, and every via hole ≥ 0.1 mm from a pad opening (bare test pads may carry in-pad vias)") | A CAM_RX_WIRE via's hole lies partly inside the pad and mask opening of **R100 pad 1** (bottom-side 0603 1 kΩ, pasted and reflowed). Solder can wick into the hole, or JLC's via-plugging ink can sit in the pad, so the joint may be starved. The defect has been on the board since R6 (R6 moved R100 to B.Cu, `sources/r6_final_objectives_review.json`), and R7 translated it unchanged. Nothing catches it: DRC hole clearance does not test a hole against a pad of the same net, `check_r7.vias_on_through_pads` covers only through-hole pads, and ORDERING lists only TP122 as an in-pad via. Impact: the camera UART RX path only. Not safety-relevant. | pcbnew: R100 at (43.0, 56.65), B.Cu, pad 1 at (42.175, 56.65), 0.8 × 0.95 roundrect (y 56.175–57.125). Via at (42.175, 56.2731): drill 0.30, pad 0.60, net CAM_RX_WIRE. The hole spans y 56.123–56.423, so 0.248 mm of it is inside the pad opening. Gerbers: `m3-B_Paste.gbr` and `m3-B_Mask.gbr` both flash the 0.8 × 0.95 aperture at (42.175, −56.650); `m3-PTH.drl` T1 (0.300) at X42.175 Y−56.273. R6 board (`git show 3b215ba:…m3.kicad_pcb`): the same via at (42.175, 38.2731). A scan of every via against every pad mask opening finds only three overlaps: R100.1, TP122.1 (bare test pad, allowed) and J2.1 (TC2030 contact, bare, allowed; hole 0.14 mm into the opening) | Move the via so its hole edge is ≥ 0.1 mm outside the pad (centre y ≤ 55.925 at the same x), or re-route CAM_RX_WIRE. Add an SMD-pad via-in-pad check, excepting bare test pads, to `tools/check_r7.py`. List J2.1 next to TP122 among ORDERING's expected DFM queries. |
| DFM-02 | Minor | M2 (paste), F10 (DNP placeholders) | The four DNP pi-network shunts C303, C305, C313 and C314 keep their **F.Paste apertures**. JLC will print paste on eight unpopulated 0402 pads, each with one pad on an RF line and the other on GND. They become solder bumps. A bridge, improbable at the 0.34 mm gap, would short the antenna port to GND (radio: the PA into a short). ORDERING says these parts are in no BOM and no CPL, which is true, but it does not mention the paste. | `m3-F_Paste.gbr` 0.500 × 0.540 flashes at (11.07, 7.13), (11.91, 7.13), (14.65, 7.13), (15.49, 7.13), (29.76, 7.60), (30.60, 7.60), (33.34, 7.60), (34.18, 7.60). The pcbnew footprint attributes are DNP, no BOM and no position file. | Remove paste from the four DNP footprints (pad paste layers off, or a large negative paste margin). Otherwise state in ORDERING that the DNP pads are pre-tinned on purpose. |
| DFM-03 | Minor | ORDERING §3 (rails/tabs), pass-1 L4 (open) | The forward 50 mm (y 68–118) has no tab, and ORDERING records this as open. JLC's own guidance is **4–6 tabs for a board longer than 100 mm** (R7 has 3). ORDERING rules out the forward short edge ("Nothing on the forward edge either") without a reason, yet that edge has windows that meet every ORDERING rule and JLC's 2 mm connector keep-out. Physical risk, Inference: printing and placement support the board from below, so the risk is lower than pass 1 rated it. A 50 mm self-weight cantilever sags about 0.01–0.03 mm at reflow (δ = wL⁴/8EI, E ≈ 5 GPa hot). The remaining risk is JLC adding its own tabs near C120/Q120/Q121, or querying the order. | My scan (courtyard and pad boxes, both sides, the ORDERING rules ≥ 1.5 mm to parts and ≥ 5 mm to capacitors, R166, LED2 and TH): long edges, no compliant start forward of y 63.0 (left) or 66.5 (right). Forward edge y = 118: compliant everywhere. x 6–11 and x 35–40 are ≥ 2.06 mm from J1 and ≥ 7.45 mm from C76. x 0–5 is exactly 5.0 mm from TH3. The forward M3 holes' edges are 2.0 mm behind the edge at x 2.4–5.6 and x 40.4–43.6, so keep tabs off those webs. JLC blog: https://jlcpcb.com/blog/pcb-mouse-bites ("Over 100 mm: 4 to 6" tabs; "Tab edge to nearest component or solder pad: 1.5 mm"; "Tabs near connectors: keep-out of at least 2 mm") | Add a forward rail with one or two 5 mm tabs at Gerber X 6–11 and/or X 35–40, Y −118 (a customer panel, or an explicit request to JLC). Otherwise keep the explicit JLC confirmation in Confirm Production file. Recheck the J1 wire entry after nibbling (the stub must be filed flush). |
| DFM-04 | Minor | ORDERING §3 | The only compliant left-edge tab, Gerber Y −68…−63, is **1.83 mm from J3's courtyard**. J3 is the USB-C receptacle, which also overhangs that edge by 0.45 mm. That meets ORDERING's 1.5 mm rule but not JLC's ≥ 2 mm keep-out for tabs near connectors. Nibbling there stresses J3's shell joints, which ORDERING already asks to be hand-finished. | Scan: J3 courtyard 1.83 mm, J3.3 pad 2.67 mm from the window; no other compliant left-edge start between y 23 and 118. Compliant left-edge starts exist at y 12.0–17.5 (in the RF strip) and y 0–2. | Either accept it with JLC's "one or two fewer holes" near connectors, nibbling the J3 side last; or use a strip window (Gerber Y −22…−12, ≥ 5 mm from both modules, check U30) plus the forward-edge tab from DFM-03. |
| DFM-05 | Minor | M1 (THT step), P3 | The **ESD diodes sit 0.50 mm from the hand-soldered SMA centre pads**, and the diode's GND pad is one of the two nearest pads. JLC solders the centre contact by iron after both reflows, next to an already-reflowed TSLP-2-20 (0.31 mm tall). Excess solder, or the diode moving as it remelts, can bridge the RF line to GND. ORDERING's post-delivery and RF bench steps have no DC check of the jack centre to GND before the first power-up or transmission. | SMA pad 5: x 12.25–13.45, y 0.2–4.4 (J30); x 30.94–32.14 (J31). D30.2 (GND) x 13.325–13.675, y 4.9–5.5, gap **0.50 mm**; D31.2 (GND) gap **0.50 mm**; D30.1/D31.1 (RF net) also 0.50 mm. Courtyard gap J30–D30 0.10 mm. Kinghelm drawing: legs 4.0 mm long, so the joint ends at the pad end y 4.4. | Order remark: "inspect D30/D31 after soldering J30/J31". Add to ORDERING §5 (after delivery) an ohmmeter check of J30 and J31 centre to shell before any power-up. Expect J31 open at DC (the ESD103 is a TVS). Expect J30 to read like a diode into the unpowered bias path (L30, then Q30's body diode), not a short (Inference). In a later revision, move D30/D31 ≥ 1 mm from the pad end. |
| DFM-06 | Minor | M1 (hand soldering), pass-1 L12 | The SMA ground-leg pads are **solid-connected** (GND_F/GND_B pad connection "THT thermal": SMD pads solid) to the F.Cu and B.Cu pours. **37–39 stitching vias per jack lie within 1 mm**, the nearest at a 0.20 mm copper gap (hole edge 0.35 mm). Pass 1 L12 asked for fence vias ≥ 0.8 mm from the leg pads. With four GND planes stitched right at the pads, hand soldering the legs is strongly heat-sunk, so cold leg joints are a realistic first-article defect. These vias also sit at ORDERING's own 0.35 mm "cannot be ink-plugged" boundary. ORDERING asks for board preheat. | pcbnew: J30 pad 1 nearest vias at (9.2, 1.0/2.3/3.6) and (11.4, 1.0/2.3/3.6), copper gap 0.200 mm, drill 0.3. J31 the same at x 27.89/30.09. Zones: GND_F/GND_B pad connection `tht_thermal`; the "Small GND pad thermal relief" DRU rule only sets spoke and gap values. | Keep the preheat remark and add "X-ray or visual check of all four leg fillets, top and bottom" to ORDERING §5. If a respin happens, move the leg-side vias out to ≥ 0.6–0.8 mm (RF reviewer to confirm the launch). |
| DFM-07 | Minor | M2 (paste) | U30's u-blox T-paste extensions for **GND pins 10 and 12 print over two tented GND stitching vias**. The paste lands on mask over a plugged via, which can steal solder through an incomplete plug or leave a dimple under the print. Same net, so there is no short risk. | `m3-F_Paste.gbr`: pin 12 outer aperture 0.8 × 1.4 at (12.61, 9.40), x 12.21–13.01, y 8.70–10.10; pin 10 outer aperture 0.7 × 1.4 at (14.81, 9.40). `m3-PTH.drl` T1 0.3 vias at (12.86, 8.83) and (14.56, 8.83). Board setup: tenting front/back yes, plugging no (ORDERING orders "Plugged"). | Move these two RF-line stitching vias out of U30's paste T (y ≤ 8.4, or shift in x), checking the GCPW fence pitch with the RF reviewer. Otherwise accept. |
| DFM-08 | Minor | M1 (reflow ratings), R7P1-13 (open) | **The LS120 reflow rating is readable and meets Standard PCBA.** Huaneng MLT-5020 datasheet item 9 "Soldering Test" (figure, p. 3): peak 250 °C max, ≤ 10 s above 245 °C, preheat 170–190 °C for 90 ± 30 s, ramp ≤ 4 °C/s. ORDERING §4 still says the rating "has not been read … confirm it allows 240 ± 5 °C before ordering", and `procurement_catalog.json` records only dimensions. | https://datasheet.lcsc.com/datasheet/pdf/23f5c6599ed9cb614c21ac31ad2b1106.pdf?productCode=C94598, p. 3, item 9 (read here from a 400 dpi render) | Record it in the catalog and in ORDERING §4/M1, and close R7P1-13. |
| DFM-09 | Minor | M1 (reflow) | **The MAX-F10S peak is u-blox's 245 °C, exactly JLC Standard's upper bound** (240 ± 5 °C), with time above liquidus 40–60 s. u-blox warns that exceeding it "may permanently damage the module". ORDERING cites the 245 °C peak but no TAL, and M1's rating list names only U5 and C84. The E22's profile (peak 230–250 °C, TAL 30–90 s) fits. EBYTE publishes no MSL for the E22 (Inference: JLC handles its own stock). | MAX-F10S IM UBXDOC-963802114-12892 R01 §5.2 (p. 71): "Peak reflow temperature: 245 °C", "Limit time above 217 °C liquidus temperature: 40 – 60 s". EBYTE E22-900MM22S manual §7.1 (p. 8). | Add to the order remarks: "final (top) reflow peak ≤ 245 °C, TAL 40–60 s (MAX-F10S)". Add U30 (245 °C) to M1's list. |
| DFM-10 | Minor | F8 (labels), AGENTS §3 (silkscreen) | The antenna legends are split across sides: **GNSS on F.SilkS, RADIO on B.SilkS**. ORDERING §7 tells the user to label the leads "GNSS and **915**" and the BOM calls J31 "915MHZ ANT SMA", so the lead label does not match the board legend. Also, FB31's designator (F, at (37.42, 22.1)) sits nearer C310's courtyard (1.52 mm) than its own (1.73 mm), just below C310 and beside "C310", against AGENTS' "never next to another part". The other designators and legends are ≥ 1.0 mm / 0.15 mm, and the 90 hidden refs match `docs/M3_R7.md` exactly. | Silk texts: 'GNSS' F (8.05, 8.10), 'RADIO' B (31.14, 7.90). ORDERING §7 Antennas row. Designator distance scan (same side, text centre to courtyard box). | Use one name (RADIO or 915) on the silkscreen, BOM comment and ORDERING §7. Put both jack legends on the same face if a spot exists. Move FB31's designator west or below FB31. |
| DFM-11 | Minor | M1 (BOM) | The JLC BOM lists the **same LCSC code on separate lines**: C530661 (J30 and J31 split by Comment), plus the inherited C430601 (J121/J124) and C307331 (two comment spellings). JLC's BOM matcher may query or double-handle duplicate part numbers (Inference: not verified against JLC's tool). The cost and stock tools already merge by code, so there is no cost or stock error. | `fab/m3_bom_jlc.csv`: 95 lines, 92 codes; the duplicated codes are C530661, C430601 and C307331. | Merge BOM lines by LCSC code in `export_fab.py`, or confirm JLC accepts it in the BOM-matching step. |

## 3. Footprints against maker drawings and JLC/EasyEDA

| Ref / footprint | Maker source | Copper | Mask | Paste | Courtyard | EasyEDA match (`jlc_corrections.json`) | Verdict |
|---|---|---|---|---|---|---|---|
| U30 `M3_MAX_F10S_LCC18` | MAX-F10S IM R01 Fig. 25/26 (p. 68); DS R03 Table 21 (p. 17) | 18 pads 1.8 × 0.8 (corners 0.7) at 1.1 mm pitch, x ±4.75: 0.8 mm outside and 1.0 mm inside the 9.7 mm body edge = Fig. 25 | = copper (board pad-to-mask 0; u-blox: "copper and solder masks have the same size and position") | T-shape: inner 0.9 × 0.6 (0.5) from 7.9 to 9.7 mm span, outer 1.4 × 0.8 (0.7) to the 12.5 mm span = Fig. 26 (150 µm stencil) | ±6.4 × ±5.95: covers the 12.5 mm paste and the P ≤ 0.6 mm tab on either 9.7 mm edge (A max 10.7) | GPS-SMD_MAX-F10S-00B, θ 0, residual 0.05 (EasyEDA pads 0.05 mm further out) | OK. Stencil 0.10–0.12 mm against u-blox's 150 µm is accepted in ORDERING. MSL 4 (DS Table 22) is in the remarks |
| U31 `M3_E22_900MM22S` | EBYTE E22-900MM22S manual ch. 3 (p. 4): 10 × 10, 20 stamp holes at 1.27, pin 1 at 2.46 mm, bottom pad 0.80 × 0.75 | 1.5 × 0.9: 0.8 inside (0.75 + 0.05 heel), 0.7 toe (derived, Inference) | = copper, web 0.37 mm | = pad | ±5.85 (0.15 beyond the pad toes) | WIRELM-SMD_20P-L10.0-W10.0-P1.27-TL, residual 0.000 | OK. Pin order counter-clockwise from the top view matches the drawing and the EasyEDA numbering |
| J30/J31 `M3_SMA_KH_KE8_EDGE` | Kinghelm KH-SMA-KE8-G drawing 2019-08-10 (LCSC p. 2): 13.5 overall, legs 4 long, 0.9 sq at 4.2/6.0, slot 1.7, flange 6.5 sq | 1.2 × 4.2 at x 0, ±2.55, y 0.2–4.4; legs 1/2 + centre 5 on F.Cu, legs 3/4 on B.Cu | 3 top + 2 bottom openings = copper | **none** (confirmed in both paste Gerbers) | F/B ±3.5, y −9.75…4.65, crossing Edge.Cuts on purpose | CONN-SMD_KH-SMA-KE8-G, offset (0, −2.3). **EasyEDA's silkscreen and 3D origin put the body toward −y, as ours does**, so rotation 0 is right (the pad pattern alone cannot tell 0° from 180°) | OK. JLC lists C530661 as "Plugin". Edge copper 0.2 mm (L6 accepted) |
| D30/D31 `M3_TSLP_2_20` | ESD103-B1-02 DS rev 1.3 Fig. 14 (p. 12): copper 0.6 × 0.35, gap 0.3; stencil 0.45 × 0.28, 0.93 overall | 0.35 × 0.6 at ±0.325 = Fig. 14 | **Per-pad openings, zero expansion, 0.30 mm web** (Infineon: one common opening). Documented deviation (stepA §6, ORDERING remark) | 0.28 × 0.45 at ±0.33 = Fig. 14 | ±0.65 × ±0.45 | TSLP-2-20_L1.0-W0.6-P0.65-BI, residual 0.005 | OK (known deviation) |
| L30 `M3_LQG15_0402` | Murata JELF243B-0010 §11.1: a 0.4, b 1.4–1.5, c 0.5–0.6; paste 100–150 µm | gap 0.40, overall 1.45, width 0.55 | = copper | = pad | ±0.88 × ±0.43 | L0402, residual 0.043 | OK. Peak 260 °C/10 s, 2 cycles (§11.3) |
| FB30/FB31 `M3_BLM18K_0603` | Murata JENF243A-0003 §10-1, BLM18K reflow: a 0.7, b 1.8–2.0, c 0.7 | gap 0.70, overall 1.90, width 0.70 | = copper | = pad | ±1.1 × ±0.55 | L0603, residual 0.05 | OK |
| Q30–Q32 SOT-23 (EasyEDA land) | EasyEDA / JSCJ | 1.0 × 0.65, rows 2.0 mm | = copper | = pad | ±1.65 × ±1.5 | C15127 0.15, C105432 0.235 (S8550 EasyEDA LS2.8), C20917 0 | OK |
| R/C 0402, 0603, 0805 (house) | IPC-7351 class | unchanged R6 lands | = copper | = pad | enclose pads | residual ≤ 0.072 | OK |

`tools/jlc_orient.py --verify-cpl` (KiCad Python, rerun here): 92 top and 119 bottom rows rebuilt from JLC
footprints, worst residual 0.491 mm (R134, R6), errors none, 8 placement-only rows, 219 rows expected. The
bottom-side rotation convention is still the documented Inference (jlc_orient docstring); confirm it in JLC's preview.

## 4. Fabrication package

- `tools/fab_manifest.py`: **OK**, 5 outputs bound to the current CAD and tools (the board hash in the manifest
  is `03fe7572…6d54`).
- **Independent regeneration:** `python3 tools/export_fab.py --out <scratch>` writes the same report lines
  as ORDERING §1 (95 BOM lines, 219 placed, no missing LCSC, no owner-fitted parts, DNP placeholders
  C303/C305/C313/C314, no uncorrected rows). The BOM and CPL are byte-identical to `fab/`. All 11 Gerbers,
  both drill files and the job file are identical once the creation-date lines are removed.
- **Zone fills:** a native `ZONE_FILLER` refill in memory changes no zone area (max 0 mm²), so the plotted
  copper is current.
- **Gerbers:** F/In1/In2/B copper, both masks, both pastes, both silks, Edge.Cuts. Edge.Cuts: a 46 × 118
  outline plus 7 Ø3.2 circles (5 M3 holes and 2 tie holes, milled).
- **NPTH:** Ø0.600 J3 locating holes (5.81, 72.41/78.19); Ø0.991 TC2030 holes; **Ø1.152 TH1 (44.8, 27.2),
  TH2 (1.4, 82.6), TH3 (1.4, 112.0)**, as in ORDERING §4.
- **PTH tools:** 0.3 / 0.6 / 0.8 / 1.1 / 1.6 mm.
- **Job file:** revision M3-ASSY-R7, 4 layers, 1.6 mm, ENIG. Stackup 0.035 / 0.203 / 0.030 / 1.03 / 0.030 /
  0.203 / 0.035 = JLC041611-7628 (1.566 mm laminate).
- **BOM ↔ CPL:** 219 refs in both, with no extra or missing ref. 96 top / 123 bottom. The top has 5
  THT parts plus J30/J31. Test pads: 3 top, 21 bottom; with J2 and TH1–3 they carry no part. All of these
  match ORDERING §4.
- **CPL rotations of the new parts:** U30 90°, U31 180° (offset 0.1 µm), J30/J31 0° at the pad centre
  (y −2.3). Bottom parts: Q30 0, Q31 90, Q32 180, R300/R302 270, R301 0, R303 180, R306/R313/R315 90.
  All are verified by the tool above.
- **DNP placeholders:** absent from the BOM and CPL. **They still have paste** (DFM-02).
- **SMA jacks:** the BOM Assembly column is "THT (JLC through-hole step, hand-soldered after reflow; no paste;
  body overhangs the aft edge)". No paste in F/B_Paste. Mask: 3 openings top, 2 bottom per jack.
- **Assembly PDFs:** every footprint has a Fab designator (scan), and the top PDF text contains U30, U31,
  J30, J31, D30, D31, L30, FB30, FB31, C303, R304.

## 5. Rails, tabs, tooling holes

ORDERING's three windows remeasured (courtyard and pad boxes, both sides):

| Window | Nearest part | Nearest capacitor/R166/LED2/TH | ORDERING says |
|---|---|---|---|
| Left x = 0, y 63–68 | J3 courtyard 1.83 mm (connector: DFM-04) | C84 5.23 mm | 1.83 / 5.23 |
| Right x = 46, y 62–67 | TP75 1.95 mm | C11 6.60 mm | 1.95 / 6.6 |
| Right x = 46, y 8–13 | C310 8.38 mm | C310 8.38 mm; U31 courtyard 10.3 mm | 8.38 / 8.38 |

Compliant 5 mm starts: left y 0–2, 12.0–17.5 and 63.0 only; right y 0–16.0 and 61.5–66.5. Forward edge:
compliant across its width (DFM-03); aft edge: excluded by the jacks. The SMA bodies (9.5 mm) clear any
long-edge rail. TH1–TH3 are vestigial for Standard PCBA and ≥ 14 mm from every tab.

## 6. Silkscreen (AGENTS §3, REQUIREMENTS M2)

- Every visible designator and legend is 1.0 mm tall with a 0.15 mm stroke. There are no small visible refs.
- The 90 hidden designators equal the `docs/M3_R7.md` list (set difference empty). All 219 + test-pad
  footprints keep a Fab designator.
- `tools/check.sh` silk check: 0 stroke points outside the outline. No new-footprint silk intersects a pad
  mask opening (polygon scan of U30, U31, Q30–Q32, J30, J31, D30, D31, L30, FB30, FB31).
- Gerbers are exported with `--subtract-soldermask`.
- Legends: GNSS (F), RADIO (B), TP30 SAFEBOOT (F), M3-ASSY-R7 (B), JLCJLCJLCJLC (B, (22.9, 85.4)), all as
  ORDERING states. Naming and placement nits are in DFM-10.

## 7. Procurement and cost (live JLC parts API, 2026-10-16 05:48Z, 92 codes, `searchType` 2)

- **Every line is in stock for 5 boards except U4** (C26633007: stock 0, `canPresaleNumber` −33),
  documented as consigned (ORDERING §1, M1).
- New lines (stock / pre-order number / need):

  | Line | Stock | Pre-order no. | Need |
  |---|---:|---:|---:|
  | C30005563 MAX-F10S | 18 | 10 | 5 (reserve; thin by ATP) |
  | C5333985 E22 | 462 | 420 | 5 |
  | C530661 SMA ("Plugin") | 959 | 829 | 10 |
  | C535146 ESD103 | 221 | 216 | 10 (+5 `leastPatchNumber`) |
  | C88980 | 62,458 | | 10 |
  | C97998 | 23,959 | | 5 |
  | C22810 | 265,919 | | 5 |
  | C15127 | 722,095 | | 5 |
  | C105432 | 210,430 | | 5 |
  | C19702, C15195, C17168, C25091, C25105 | > 1 M | | |

- **J9** (C161692) shows `canPresaleNumber` −2358 against 1,088 in stock. JLC's own part page renders
  `canPresaleNumber 0` beside `overseasStockCount 1088`, so the field is the private-library pre-order
  allowance, not PCBA stock. Treat J9 as in stock (Inference).
- **Cost (M3), with my own computation from live prices:**
  - parts $82.78 per board; with JLC minimum purchases $84.20;
  - plus 92 × $1.53 / 5 = **$110.93 per board** against the $126.41 cap;
  - **52 extended codes** against the 52 limit (margin 0);
  - this agrees with `fab/cost_check.json` (05:15Z snapshot).
- `tools/check_procurement.py --cost-only`: OK. The full gate fails on U4's stock, as documented (R7P1-18:
  the tools have no consignment path).
- **JLC consignment page** (https://jlcpcb.com/help/article/how-to-consign-parts-to-jlcpcb):
  - parts are shipped to JLC's HK warehouse after approval;
  - price review takes ≤ 2 business days;
  - handling fee 2 % (minimum USD 10) per shipment, with refundable duty/VAT deposits;
  - none of this is in M3 (ORDERING excludes the consigned U4 from the target).

## 8. Assembly process (reflow, MSL, THT step)

- **Reflow ratings against Standard's 240 ± 5 °C:**

  | Part | Rating | Source |
  |---|---|---|
  | MAX-F10S | peak 245 °C, TAL 40–60 s | IM §5.2; DFM-09 |
  | E22 | 230–250 °C, TAL 30–90 s | §7.1 |
  | LQG15, BLM18 | 245 ± 3 °C typical, 260 °C/10 s ×2 | |
  | MLT-5020 | 250 °C max | DFM-08 |
  | Kinghelm SMA | wave 240–250 °C, 5 s; hand-soldered (L8) | |

- **MSL:** MAX-F10S MSL 4 (DS Table 22), with the bake remark in ORDERING. E22: none published.
- **Reflow order:** both modules on the top, which ORDERING asks to be reflowed last (u-blox: "single final
  upright reflow"). The limiter parts under U30 are on the bottom (two reflows, small SOT-23/0402).
- **Through-hole step:** the jacks are fitted after both reflows, by hand.
  - The overhang only has to clear the panel at that step; there is no rail on the aft edge.
  - Slot 1.7 ± 0.2 mm against a pad stack of about 1.64 mm nominal (1.566 laminate + 2 × 0.035 Cu,
    Inference) and JLC ±10 %: a bench fit check is in ORDERING §5 (L9).
  - Heat-sinking and the nearby diodes: DFM-05 and DFM-06.

## 9. Sources

- u-blox MAX-F10S integration manual UBXDOC-963802114-12892 R01:
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_IntegrationManual_UBXDOC-963802114-12892.pdf
  - §4.4.1, Fig. 25–26, p. 68;
  - §5.2, p. 70–72.
- u-blox MAX-F10S data sheet UBXDOC-963802114-12732 R03:
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_DataSheet_UBXDOC-963802114-12732.pdf
  - Table 21, p. 17;
  - Table 22, p. 18.
- EBYTE E22-900MM22S manual: https://datasheet.lcsc.com/datasheet/pdf/70331b0eaf0eedaea0129e9e66d9a011.pdf?productCode=C5333985
  - ch. 3, p. 4;
  - §7.1, p. 8.
- Kinghelm KH-SMA-KE8-G: https://datasheet.lcsc.com/datasheet/pdf/35ad22a9bea57e53d493009a20c931ef.pdf?productCode=C530661
  - p. 1, wave solder 240–250 °C 5 s;
  - p. 2, drawing.
- Infineon ESD103-B1-02 series rev 1.3: https://datasheet.lcsc.com/datasheet/pdf/9f837311bec7e3ead15a9d62fb0575b0.pdf?productCode=C535146 (Fig. 13–14, p. 12).
- Murata LQG15HS JELF243B-0010: https://datasheet.lcsc.com/datasheet/pdf/4fdc9bb2296ffef8346418b98de47ce9.pdf?productCode=C97998 (§11.1, §11.3).
- Murata BLM18KG JENF243A-0003: https://datasheet.lcsc.com/datasheet/pdf/2d503a4b167da9bb5d0eb4a3fa711314.pdf?productCode=C88980 (§10-1).
- Huaneng MLT-5020: https://datasheet.lcsc.com/datasheet/pdf/23f5c6599ed9cb614c21ac31ad2b1106.pdf?productCode=C94598 (p. 3, item 9).
- EasyEDA footprint for C530661 (silkscreen, 3D origin): https://easyeda.com/api/products/C530661/components
- JLC parts API: POST https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList.
  - J9 page: https://jlcpcb.com/partdetail/JST-BM04BGHSTBT_LF_SN/C161692
- JLC mouse-bite guidance: https://jlcpcb.com/blog/pcb-mouse-bites
- JLC consignment guide: https://jlcpcb.com/help/article/how-to-consign-parts-to-jlcpcb

## 10. Inferences (not measured, or not from a primary source)

- The E22 land toe and heel (EBYTE gives the module pad only; the land equals JLC/EasyEDA).
- The cantilever sag estimate (E ≈ 5 GPa above Tg) and the statement that JLC supports the board from
  below during printing.
- The meaning of `canPresaleNumber`, inferred from JLC's part page.
- That JLC's BOM matcher queries duplicate codes (DFM-11).
- The SMA pad-stack thickness against the 1.7 mm slot.
- That E22 MSL handling is covered by JLC's own stock control.
- The expected DC readings at the jacks in DFM-05.
- The JLC bottom-side CPL rotation convention, inherited from the jlc_orient docstring and not re-derived
  here.

## 11. Method (reproducible, read-only)

KiCad 10.0.6 Python (`pcbnew.LoadBoard`, never saved) scripts in the session scratchpad:
- placement and attribute dump;
- zone pad-connection styles;
- via-against-pad-opening polygon scan (`TransformShapeToPolygon` with the mask expansion);
- via-under-paste scan;
- SMA pad neighbours and vias;
- tab-window scans on all four edges;
- designator-to-courtyard proximity;
- hidden-ref set comparison;
- native refill area comparison.

The rest of the method:
- Gerber flash parser over the unzipped `fab/m3_gerber.zip`;
- `kicad-cli pcb drc --severity-all` on a temporary copy (0 violations, 0 unconnected);
- `tools/check.sh` (exit 0);
- `tools/fab_manifest.py` (OK);
- `tools/jlc_orient.py --verify-cpl` (OK);
- `tools/export_fab.py --out <scratch>` (identical outputs);
- live JLC API queries for all 92 codes.
