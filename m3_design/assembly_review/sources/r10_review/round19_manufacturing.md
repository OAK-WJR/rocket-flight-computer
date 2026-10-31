# Round 19 manufacturing review

Target 1e60441, board a3144b15 (unchanged before and after). Totals: 0 Critical, 0 Major, 4 Minor.

## R19-MFG-01 (Minor) RADIO legend sits on the J410/J420 seam and reads as J410's
- Evidence: m3.kicad_pcb F.Silkscreen text RADIO: ink y 23.03-24.03 mm, right edge x 34.5. J410 courtyard y 8.05-24.07 (pads y 10.25-20.75), J420 courtyard y 24.05-40.06 (pads y 26.25-36.75). Ink lies wholly inside J410's span, 0.02 mm above J420's; nearest pad 2.75 mm to both (J410.1 y 20.75, J420.4 y 26.25). GPS (ink y 9.2-10.1) and CAM (y 44.4-45.4) sit inside their own connector's span at its pin-4 end. Both connectors have the same 4V8/GND/TX/RX order. D-R18-11 itself records the tie as the one WORD_SEAMS entry. Region x 29.8-34.6, y 24.6-27.4 on F.Cu has no footprint, pad or track (pcbnew query).
- Impact: A person wiring the harness can plug the radio into J410 and the GPS into J420 (same pinout, same connector): UART6/UART5 swap, GPS and telemetry dead until found. Not a hazard (ports cannot arm or fire), but a pad-time wiring error.
- Fix: Move RADIO to y about 26.0 (ink 25.5-26.5, still right-justified at x 34.5): 1.43 mm from J410 courtyard, inside J420's span, beside J420.4. Then delete the RADIO WORD_SEAMS tie in check_r10 and r10_post.

## R19-MFG-02 (Minor) C84 lands carry solder paste in the JLC Gerbers although C84 is not placed; no record says what JLC will do with it
- Evidence: pcbnew: C84 (27.5,78.5) rot 90, pads 1 (VLOGIC) and 2 (GND), each 3.5 x 1.7 mm on F.Cu / F.Mask / F.Paste. F.Paste flashes = 243 other + 2 C84 = 245 (matches the manifest count); B 359 + 12 J430 = 371. C84 is absent from m3_bom_jlc.csv and m3_cpl_jlc.csv (D-R18-09). grep of docs/ORDERING.md, M3_R10.md and R10_DECISIONS.md finds no statement that the C84 lands are pasted.
- Impact: JLC prints and reflows paste on both C84 lands with no part: two domed solder blobs (about 6 mm2 each at the stencil thickness), or a JLC query. The manual OS-CON fit then sits on a dome / uneven fillet, and the polymer cap is fitted onto already-reflowed solder, which ORDERING 8.2 does not describe (it says only "absent from both passes").
- Fix: Choose and write down: (a) remove F.Paste from the C84 pads in the footprint (hand-paste or hand-solder; update paste_check to 243 top), or (b) keep it and add to ORDERING 8.2 and the order remark that the lands arrive with reflowed solder and are re-flowed locally during the manual fit.

## R19-MFG-03 (Minor) ORDERING.md line 100 still states the pre-D-R18-08 U4 mask values
- Evidence: docs/ORDERING.md line 100: "+0.025 mm mask relief ... preserve its 0.100 mm individual mask webs". Same file lines 377-379 and the board: U4 pad local mask margin 0, min pad gap 0.150 mm (pcbnew, pads 0.575 x 0.35 at 0.5 mm pitch).
- Impact: An order remark or a JLC CAM query built from line 100 asks JLC to hold 0.100 mm webs and +0.025 mm relief, which no longer match the Gerbers.
- Fix: Edit line 100 to "mask relief 0, 0.150 mm webs" (or point to the section 8 text).

## R19-MFG-04 (Minor) Pin legends 1:BAT+, 1:SW and 1:5V4 lie under or at the edge of the 3D connector bodies
- Evidence: 3D render (kicad-cli, top): 1:BAT+ (J1.1, text centre 6.0,71.4, ink y 70.9-71.9) is cut by the J1 body, which starts near y 71.5 in the model; 1:SW (J400.1, x 2.9, y 63.3, ink x 2.4-3.4) clipped by the body edge x 3.0; 1:5V4 (J9.1, 41.7,55.55) clipped at J9 body end y 55.9. The F.Fab outlines (J1 x 3.85-11.35, y 72.3-79.4) show no overlap, so the model and F.Fab body disagree; courtyards (J1 y 70.98-79.8) do contain these legends.
- Impact: Inference (real DB125 body not measured here): the battery polarity and camera supply legends may be partly hidden by the housings on the finished board.
- Fix: Check the DB125 body outline in the DIBO datasheet and move these three legends at least 1 mm outside the body / courtyard (e.g. 1:BAT+ to y 69.9 is blocked by J400, so use the west or board-edge side).

## Fix verification
- D-R18-08: confirmed. L400 pads 2.0 x 1.8 mm at x 21.95 / 26.45 (+/-2.25, gap 2.50, outer 6.50) equal Bourns SRP5030T datasheet Recommended Layout 6.50 / 2.50 / 1.8 (https://www.bourns.com/docs/Product-Datasheets/SRP5030T.pdf, p.1). U4 margin 0, gap 0.150.
- D-R18-09: confirmed (paste side effect open). BOM designators 197 unique, qty column sums match, CPL 197 rows, no BOM/CPL mismatch, LCSC fields equal board for all 197; owner BOM = C84 only; paste 245 F / 371 B recounted. Side counts 66 top / 131 bottom match docs. Side effect: see R19-MFG-02.
- D-R18-11 manifest: confirmed. all six output SHA-256 recomputed equal; 193 input hashes recomputed, 0 mismatch; input list contains m3.kicad_pcb a3144b15.
- Gerber zip: confirmed. Re-exported 11 Gerbers with the same kicad-cli 10.0.7 command as export_fab.py: all 11 byte-equal after removing timestamp lines; both drill files body-equal; job file differs only by date.
- Silkscreen hidden designators: confirmed. visible refdes 120, hidden 88 of 208; no visible refdes or legend under 1.0 mm height or 0.15 mm stroke.

## Closed candidates
- DRC all severities with schematic parity: 0 violations, 0 unconnected, 0 parity (kicad-cli 10.0.7).
- Vias under 0603 bodies (R86, R89, R91, R101, R401, R403): all 292 vias are tented on both sides; each via is centred in the pad gap with 0.175 mm edge gap to each pad; no mask opening, so no wicking path. Closed.
- Via ring 0.5/0.3 (ring 0.10 mm): JLC states via diameter must be 0.1 mm (0.15 preferred) over hole; ours is +0.2. Closed. The 0.15 mm absolute PTH ring applies to component holes (1.9/1.3 rings 0.3).
- J3 plated slots 0.6 mm wide (4, G85 in PTH.drl): JLC multilayer minimum 0.35 mm, length >= 2 x width (1.4/1.7 >= 1.2). One older source quotes 0.65 mm; confirm in DFM. Closed as qualified.
- Mask webs: no pad pair on one layer below 0.15 mm except same-pad Q120/Q121 exposed-pad merges; JLC green minimum 0.10 mm. Closed.
- Silk stroke 0.15 mm on 1.0 mm text is JLC's floor (preferred 1:6 would be 0.167 mm). Closed.
- No fiducials on the board: JLC Standard PCBA edge rails supply them (ORDERING). Closed.
- Order-number placeholder JLCJLCJLCJLC is on B.Silkscreen (20.35,35.6), 1.0 mm high; DRC clean. Closed.
- J430 CPL origin differs from the footprint origin by 1.55 mm: covered by tools/jlc_corrections.json (C164170) and the orientation gate. Closed.

## Coverage limits
- JLC DFM not run; JLC via-covering per-via mixing (VIPPO on U401.11) and tenting of the 1.0/0.5 BAT_IN via are process questions only JLC can answer (already in ORDERING 8.1).
- Real DB125 body size not measured (R19-MFG-04 is inference from the model).
- Gerber layers were compared by regeneration, not by an independent Gerber viewer.
- Stackup copper (inner 1 oz) not verified against a JLC quote.
