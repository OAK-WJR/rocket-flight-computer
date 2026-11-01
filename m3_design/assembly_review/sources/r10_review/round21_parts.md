# R21 parts / BOM / CPL / lands / ratings / stock (Claude)

Target commit `accfff4947266a23cf60a63f3d92be047f5391b5`. PCB SHA-256 before and after:
`0dc847761de94a45cf68b1c82ec91f38e9d4ebb7297abc7108e3df9a454940d3` (unchanged; no tracked file edited).
Evidence, sources and limits: [round21_parts.json](round21_parts.json). Probe scripts and raw supplier / EasyEDA
responses: `.supervisor/r21_parts/` (ignored).

**Totals: 0 Critical, 0 Major, 4 Minor (1 new, 3 carried).**

## Findings

| ID | Sev. | Status | Finding and key number | Fix |
|---|---|---|---|---|
| R21-BOM-01 | Minor | new | D-R20-05 removed the inner rings, so two plated terminal holes now sit **0.250 mm** from foreign inner copper: J400.2 (7.4, 67.6) to In1 GND, and J1.2 (7.4, 77.6) to In2 RAW_PROTECTED. JLC's capability page gives **0.3 mm** for "inner layer PTH pad hole to copper" (0.2 mm is the via rule). Every other plated pad measures ≥ 0.55 mm. The project rule is 0.25 mm, so DRC passes. A short would be fail-safe (U9 limits current, or EN is held low), with no fire path. | Add a `.kicad_dru` rule: through-hole pads need hole clearance ≥ 0.3 mm. Refill (each pour backs off 0.05 mm), re-check the K-plane necks, then gate it. |
| R21-BOM-02 | Minor | carried R20-BOM-01 | U4 ISM6HG256XTR live at 13:40Z: stockCount 9, canPresale **2** for 5. The alternate LSM6DSV320XTR C26633007 also shows 0 / −18 at JLC and 0 at LCSC. The gate now fails on U4, which confirms the gate fix. ORDERING line 423 still calls U4 "the stocked" part. | Buy ISM6HG256XTR from a franchised source and consign it (keeps CPL 180° and one firmware map). Reword line 423. |
| R21-BOM-03 | Minor | carried R20-BOM-02 | DB125 holes are 1.30 mm with 1.90 mm lands, against DORABO's 1.20 mm. The outer annulus is 0.30 mm, which meets JLC's rule. | First-article fill check. |
| R21-BOM-04 | Minor | carried R20-BOM-03 | VCAP C19 / C20 (C23630) have no maker-bounded worst case. | As R18-m10. |

## Fix verification

| D-ID | Verdict | Measured |
|---|---|---|
| D-R20-09 D440 / D441 | confirmed | B(4.45, 19.45) / B(4.45, 23.05), −90°. CPL Bottom 270, the same as D410 / D411. The EasyEDA rebuild is off by 0.005 mm. Paste is 0.28 × 0.45 on all pads. The barrel gap is about 1.9 mm (D410 / D420 have about 1.8 mm). The part is bidirectional. |
| D-R20-04 TP82 | confirmed | B.Cu with mask opening, no paste, excluded from BOM / POS. |
| D-R20-05 inner rings | partly | Library: a one-line change per footprint. DRC library parity is 0. The Gerbers show the rings gone at J121.1, J400.2 and J1.2 (In2). However, J400.2 and J1.2 now sit 0.25 mm from foreign copper, under JLC's 0.3 mm (R21-BOM-01). |
| D-R19-04 C123 | confirmed | C15195, 10 nF / 50 V X7R, ACT_EN / GND, residual 0.000 mm. |
| D-R19-07 C84 | confirmed | No F_Paste flash. Owner BOM only. Paste totals are 253 / 375. |
| D-R19-11 U4 | confirmed | Fresh EasyEDA (BR) at Bottom 180: 0.040 mm on all 14 pads. |
| D-R19-14 J440 | confirmed | J440 residual 0.000 mm. Identity check: 215 / 206 / 205 / 666 nodes, 0 mismatches. |

## Closed independently

- DRC (kicad-cli 10.0.7, all severities, with schematic parity): 0 / 0 / 0.
- Manifest hashes match the files.
- The 130 `LCSC Part` fields all equal `LCSC`.
- Live check: 36 Basic / 45 Extended, and every model matches its MPN.
- CPL outliers are the known land-size cases: Q124, R134, LS120, Q120 / Q121.
- D441 is 2.53 mm from J3.4's hand-finished slot. That is farther than the named C83 (1.96 mm) and R8 (2.15 mm), so this is not a finding.
- Cost: $85.35 against the $84.41 cap. This is an open owner decision; noted only.

## Fix now

R21-BOM-01: the 0.3 mm hole-clearance rule for through-hole pads, refill, gate assertion.

## Limits

- Lands that did not change are carried from rounds 19–20; today's EasyEDA pads match them.
- JLC's bottom-side rotation convention and what `canPresaleNumber` means are both Inferences.
- I did not re-run cost live.
- I did not check franchised stock.
- No physical qualification.
