# Round 21 manufacturing review

Target commit `accfff4`, board `0dc84776…`. The board SHA-256 is the same before and after the review. **Totals: 0 Critical, 0 Major, 2 Minor (both new).** Machine-readable twin: `round21_manufacturing.json`.

## Findings

### R21-MFG-01 (Minor, new): two terminal PTH walls are 0.25 mm from foreign inner copper, below JLC's 0.30 mm rule

D-R20-05 removed the unconnected inner rings of two terminal holes. That left their 1.3 mm plated holes too close to foreign inner-plane copper.

**Measured.** Hole wall to the nearest foreign inner copper, for every plated hole (pcbnew polygons):

| Hole | Net | Layer and neighbour | Wall gap | Before D-R20-05 |
|---|---|---|---|---|
| J1.2 (7.4, 77.6) | GND | In2 RAW_PROTECTED | **0.250 mm** | 0.551 mm |
| J400.2 (7.4, 67.6) | BAT_SW_RETURN (U9 EN) | In1 GND | **0.250 mm** | 0.551 mm |

- These are 2 of the 62 PTH. The next smallest gap is 0.45 mm, at J3's shell slots.
- Every via passes JLC's 0.20 mm via rule; the smallest via gap is 0.25 mm.
- The Gerbers confirm that neither hole has an inner flash on the layer concerned.

**JLC's rule.** JLC (https://jlcpcb.com/capabilities/pcb-capabilities) lists two separate figures:
- inner-layer **PTH pad** hole to copper: 0.3 mm;
- inner-layer **via** hole to copper: 0.2 mm.

Through-holes also carry a +0.13 / −0.08 mm tolerance.

**Why the gate and records missed it.**
- The DRU's only hole rule is 0.25 mm, applied to vias and pads alike, so DRC reports 0 violations.
- M3_R10 and R10_VALIDATION (row 9) record the J1.2 figure as "the hole clearance of every GND via in a RAW region". That treats a 1.3 mm component hole as if it were a via.

**Impact.** This is a DFM shortfall, not a hazard. JLC may put the order on hold. If the board is built as drawn and a short forms:
- GND to RAW_PROTECTED: U9 limits the current, so the board is dead.
- EN to GND: the board stays off, which fails safe.

JLC's bare-board E-test would catch either short.

**Fix.** Add this generated DRU rule, then refill:

`(rule "PTH hole to inner copper (JLC 0.30 mm)" (layer inner) (condition "A.Type == 'Pad' && A.Pad_Type == 'Through-hole'") (constraint hole_clearance (min 0.35mm)))`

Only those two pours should move, each back by 0.1 mm. Re-run DRC, K-plane, K-region and S-8.

### R21-MFG-02 (Minor, new): ORDERING 8.1 still gives the previous board's via inventory

The VIPPO / via-covering paragraph still describes `50a39de5…`: 301 vias, 296 of them 0.5 / 0.3 mm. The current board has:
- 302 vias: 297 at 0.5 / 0.3, 4 at 0.6 / 0.3 and 1 at 1.0 / 0.5;
- a drill file that agrees: 301 hits at 0.30 mm and 1 at 0.50 mm.

M3_R10 and R10_VALIDATION already say 302. Fix the docs.

## Fix verification

| Item | Verdict | Measurement |
|---|---|---|
| D-R20-05 | partly | The rings are absent where claimed: In1 has none at J121.1 / J400.2; In2 has none at J121.1 / J400.2 / J1.2; J121.2 keeps both. J121.1's wall is 1.050 mm. The side effect brings J1.2 and J400.2 to 0.250 mm, below JLC's PTH rule (R21-MFG-01). |
| D-R20-06 | confirmed | No visible designator is nearer another courtyard than its own. This was tested against every footprint, with no centre pre-filter. C400 is 0.118 mm from its own courtyard and 0.172 mm from J440's. C94, R461, C404, R90 and U401 are hidden. The 96 hidden designators match the M3_R10 list exactly. |
| D-R20-07 | confirmed | 217 Fab texts (fields included) give 0 crossings of their own outlines. R119, D440 and D441 are legible in the 1200 dpi PDF crops. |
| D-R20-08 | confirmed | The west aft band has In2 0 mm²; GND covers the other three layers. The east tabs still sit over RAW_PROTECTED and PORT_5V3; that is an owner decision. The T-1 windows are unchanged. D440 clears the west aft tab with 2.649 mm of margin. |
| D-R20-09 | confirmed | CPL D440 / D441 are Bottom 270, like D410 / D411. The parts are bidirectional, so polarity cannot be wrong. CPL has 72 top / 133 bottom; paste has F 253 / B 375. |
| D-R20-02 | confirmed | The FB via is present. The board has 302 vias and the drill file agrees. |
| R20-MFG-04 | confirmed | ORDERING 8.1 now has the order-number row, and the placeholder is unchanged. |
| Manifest | confirmed | 193 inputs and 6 outputs re-hashed with 0 mismatches. A fresh Gerber / drill export is identical except for the date lines. |

## Fix now

- **R21-MFG-01:** add the DRU rule above and refill. The risk is low and it brings both holes into line with the fabricator's published rule.
- **R21-MFG-02:** a one-line docs edit.

## Closed

- **DRC:** 0 violations, 0 unconnected, 0 parity, with no ignores.
- **Stackup:** 1 oz outer and 1 oz inner (0.030), 1.6 mm, ENIG, matching ORDERING.
- **Copper geometry:**
  - minimum track 0.20 mm;
  - via ring 0.10 mm and PTH ring 0.30 mm;
  - smallest via-to-via hole gap 0.259 mm.
- **Inherited spacings:** J3's NPTH pins are 0.37 mm from its slots and 0.20 mm from F copper. Both come from the vendor land and are carried.
- **VIPPO:** only the two U401.11 vias are marked.
- **BOM, CPL and owner BOM:** consistent with the board. The owner BOM uses CRLF line endings and is not uploaded.
- **Silkscreen:**
  - ink to a mask opening at least 0.156 mm;
  - ink to the edge at least 0.302 mm;
  - text to text at least 0.155 mm.
- **R463 / 3:TXO:** they are stacked 0.216 mm apart and read as two separate lines in the render.
- **Fiducials:** none on the board; JLC's rails add them.
- **Cost and stock:** the evidence predates the CPL change, and U4 has only 2 orderable. Both are disclosed owner items and are not filed.

## Coverage limits

- No JLC DFM upload or quote was made.
- Distances are measured to the drawn finished hole; drill oversize and registration are not modelled.
- The R21-MFG-01 fix was not trialled on a copy.
- Supplier stock and cost were not re-queried.
