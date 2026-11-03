# R10 round 27: mechanics lens

- Reviewer: claude. Commit `816038c`. Board SHA-256 `a0ec075e…` before and after (unchanged).
- Totals (real errors only): **0 Critical / 0 Major / 1 Minor.**

## Findings

### R27-MECHANICS-01 (doc, Minor): J440 lead route bound points the wrong way

- **What is wrong:** ORDERING 8.4's "J440 leads (R20-MEC-01)" row and the handoff's "J440 lead routing" both say to route the
  leads aft, over or around the (4, 4) head, and past the aft edge, and also to "keep them south of y 23.5". In the R10 records'
  compass, south means larger y, which is forward:
  - D-R26-01 puts the via "1.5 mm north" of J440.3: (7.4, 16.5) from the pin at y 18.0.
  - D-R26-02 moves R173 "0.65 mm north" from y 59.7 to y 59.05, which R10_VALIDATION calls "toward the aft edge (y − 0.65 mm)".
  - M3_R10 says "R173 cannot go back south".
  - ORDERING 8.3 says to brush TP122 "from south/east"; TP122 is at larger y than U5.
- **Evidence (pcbnew, `a0ec075e…`):**
  - J440's body spans y 7.93–23.45, and its wire entries are at y 11.0, 14.5, 18.0 and 21.5, all below y 23.5.
  - J3's USB-C shell spans y 26.33–35.27.
  - Leads kept at y > 23.5 must run forward along x = 0 into the J3 zone. The same row forbids that, and it is not the way to the (4, 4) head or the aft edge.
  - The intended bound is y < 23.5 (north of y 23.5).
- **Impact:** read literally, the instruction routes the AUX, GPS or radio leads toward J3, the J121 / J400 exits and the
  (4, 44.3) head. Those are the chafe and fire-class adjacencies the row exists to prevent. The procedure contradicts itself as written.
- **Fix:** in both documents, replace "keep them south of y 23.5" with "keep them aft of y 23.5 (y < 23.5; J440's forward body end
  is at y 23.45)".

## Fix verification

| Change | Verdict | Measurement |
|---|---|---|
| D-R26-01 | Confirmed | GND vias at (7.4, 16.5) and (7.4, 20.0) are 1.500 mm from their pins. Gaps: 0.300 mm to the pin's own pad, 0.800 mm to the neighbouring pin, 0.700 mm hole to hole, 0.600 mm from the via ring to the pin hole. Both vias are tented on both sides and drilled in the bound Gerbers. No conflict with fit, supports or tails. |
| D-R26-02 / -04 (mechanics) | Confirmed | Only C10, C11, R164 and R173 moved (bottom side, 0.60–0.65 mm). No terminal, support or outline changed. Fit and plate results are unchanged. C10 to the U5 coat union is 3.016596 mm (pads 3.449036 mm), matching ORDERING 8.3. |

## Plate model (re-run)

The model was re-run on `a0ec075e…` from a fresh fit report and `masses.json`:

| Quantity | Result |
|---|---|
| First mode, pinned D5 / D10 | 180.8 / 255.6 Hz |
| First mode, clamped D5 / D10 | 287.8 / 407.0 Hz |
| Mass | 78.6 g |
| Maximum deflection at 100 g | 1.27 mm |
| 100 g gap at h = 4 mm | C431 0.261 mm, C421 0.320 mm |
| 100 g gap at h = 3.5 mm | C431 −0.239 mm (overlap) |

The recorded figures hold for this board, and so do the contact loads: 125, 133, 175 and 214 g. The docs say the model was "not re-run on `a0ec075e…`". That is now stale, but it is not false.

## Checks run

- `fit_check --profile r10`: OK. Worst margins:
  - J3: 0.886 mm.
  - DB125 bodies: 2.976 mm.
  - 27 tails: 7.558 mm.
- Supports:
  - Nearest bottom part: C32.2, 4.536 mm from its support.
  - Nearest top pad: LED2.2, 3.808 mm.
  - J440 body to (4, 4): 3.930 mm.
- Wire room: 5.003 mm at all eight terminals.
- `check_r10` M-1, M-3, M-5, M-6, M-7, M-8 and P-11: OK.
- `test_fit_check`: 33 tests OK.
- Hand recalculations: the h + t bounds (6.0184 / 5.3653 mm) and the contact loads.

## Observations (8, not counted)

The JSON lists all eight. The main ones:
- M3_R10's historical section still gives C10 at 3.333144 mm. That section's heading marks it as historical.
- The east-edge strain figures in M3_R10 are labelled as `632a9ad3…` values. The current values are 1117–1421 µε.
- `tools/test_r10_plate.py` fails because its fixture lacks the J430 and J440 rows. It is not run by `check.sh`.
- The J440 vias are tented under the terminal body and violate no rule.

## Limits

- CAD envelopes only.
- The plate model uses inferred masses and stiffness.
- I did not re-read the DB125 drawing or VEHICLE.md.
