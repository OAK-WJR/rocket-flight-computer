# Round 11: fresh verification of R11-BOM-01

Independent verifier: `r11_terminal_verifier`, fresh context; target commit `21bc3b2`,
PCB SHA-256 `0c50b9fd0930f34edab7129fc21b8e71d0ee03bc079e1900b7e131cece6bfaf8`.
The coordinator transcribed this report because the validator role forbids file writes.
The verifier changed no file, CAD, Git state or service request.

**Confirmed: 0 Critical, 1 Major.** This is the same finding as R11-BOM-01 and the
mechanics lens's terminal-envelope item, counted once. It is an acceptance-bound
defect, not evidence of a physical collision or a change to AGENTS section 2.

[DORABO T0-1, sheet 1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf)
gives total depth 7.40 +/-0.30 mm and rear-face-to-pin-row distance 3.90 +/-0.20 mm.
The repeated 3.90 annotation is the same datum, counted once. The allowed wire face
reaches 7.70 - 3.70 = +4.00 mm from the pin row. Current `r10_parts.py` MODELS instead
end at +3.65 mm, with local depth -4.05 to +3.65 mm. The conservative tolerance
union is -4.10 to +4.00 mm; it does not describe an individual 8.10 mm deep body.

Using the nominal CAD pin centres, the full-length tolerance, the single 1.75 mm
end datum and the 0.42 +/-0.20 mm interlock on local -x gives these unions:

| Positions | Local x bounds, mm | Local y bounds, mm | Height, mm |
|---|---|---|---|
| 2 | -4.62 to +3.70 | -4.10 to +4.00 | 8.90 |
| 4 | -8.32 to +7.20 | -4.10 to +4.00 | 8.90 |
| 5 | -10.07 to +8.95 | -4.10 to +4.00 | 8.90 |

Independent native/in-memory controls:

- Native SHA matches the target. Baseline P-11 passes all seven terminals at
  4.953012 mm; corrected envelopes fail all seven at 4.603012 mm, 0.346988 mm below
  the accepted 4.95 mm floor. West faces can reach x3.00; east faces x43.00.
- Full fit with corrected envelopes still passes bore/support checks. Minimum
  terminal radial margin is 2.612560 mm. No current terminal/body box intersection
  was found. These are CAD calculations, not fitted-part measurements.
- Moving each row inward 0.35/0.40 mm restores room to 4.953012/5.003012 mm and
  retains bore/support passes. A move alone is incomplete: J9's corrected box then
  overlaps C60's box by about 0.0201 x0.02005 /0.0701 x0.02005 mm respectively.
- With an additional 0.25 mm courtyard margin, nearby C60/C94/R61/R104/R105 and
  west Q124/R80/R165/C80 need clearance review. Four-position courtyards span
  16.02 mm, exceeding the current 16 mm row pitch by 0.02 mm.

Concrete fix: correct the asymmetric generated envelopes and courtyards, move the
rows inward (0.40 mm proposed), legalize local neighbours/routes and retain the
4.95 mm floor. Rebuild and requalify DRC, fit, hot-plug, fabrication, binding and
reproducibility through the supervisor. Do not silently lower the floor.

Major severity follows P2's maximum-tolerance requirement and OQ-1's no-worse
floor. Earlier unqualified-fit Minors do not authorize a smaller floor. Actual
harness, screwdriver, staking and bore/stack fit remain unverified.
