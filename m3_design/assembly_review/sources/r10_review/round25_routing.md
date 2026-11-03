# Round 25 routing lens (Claude)

Target commit `c4bb56b`, board `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f` (SHA-256 identical
before and after). Probe scripts and board copies: `.supervisor/r25_routing/`.

**Totals: 0 Critical / 0 Major / 0 Minor real errors.**

## What was checked

- **AGENTS section 3 / M2 rules on every net:**
  - Off-angle: 0.
  - Every plain two-end node is 45° (393), apart from one collinear node that is counted for review.
  - The 90° bends at pads (25) and vias (10) all have the bend's inner corner inside the holder's copper.
  - The acute 45° interiors at pads (4) have their wedge covered.
- **route_check:** `route_check --profile r10 --bumps-all` reports 0 failing, 0 allowlisted, 5 unrecorded noncritical leftovers and 48 bump windows. There are no staircases, stubs, dead copper, overlap-only joints, crossings or critical hygiene instances.
- **Short segments:** every one under max(w, 0.2) lies wholly inside a pad or via of its own net. The exception is the leftover BAT_OVLO 0.15 mm segment, a noncritical review item.
- **GND partner vias:** all 25 gated critical layer changes have a GND via within 1.5 mm (0.77–1.492 mm; the tightest is PYRO1_GATE at 1.492 mm). The 11 vias over 1.5 mm are all on AUD-2's named slow list.
- **Reference planes:** check_r10's own K-region and K-reference, run on the probe copy, report 0 issues (172287 samples, 0 loose, 5 recorded strays). The In2 plane is 3V3 under 17 of the 25 gated vias, PORT_4V8 under 4, GND under 3, and PYRO1_OUT's via sits in its S-8 void, as section 6 says.
- **Vias in pads:** only U401.11's two GAP-3 vias.
- **Detour table:** recomputed at 1501.8 / 1237.8 mm (1.213×), matching section 6.

## Fix verification

- **D-R24-18: confirmed.**
  - The copper diff against `1407e850…` is exactly BAT_FAULT_N's three F.Cu pieces.
  - The BAT_ENABLE via (17.1, 82.8) clears the legs by 0.200 / 0.200 mm and the chamfer by 0.2015 mm (it was 0.1733 mm). The diagonal is 0.4525 mm.
- **D-R24-17: confirmed.**
  - `5516eeec…` had 59 bends (F.Cu 25, B.Cu 31, In2 3; 6 at pads or vias). Of its 53 plain corners, 51 are now chamfered and 2 were redrawn (the BAT_IN trunk and CAM_FAULT_N's drop).
  - Pair pitch is kept: 0.700 / 0.502 mm.
  - USB_DM is 19.29 mm and J440's clamp runs are 3.864 / 3.964 mm.
  - No chamfer is under max(w, 0.2).
- **D-R24-21: confirmed.** BOOT0's second via is cited as D-R24-03 in route_check, r10_route_core and check_r10.
- **Second barrels (D-R24-02, -03, -04, -08, -10): confirmed.** All PARALLEL_VIAS entries match, and parallel_via is 0.

## Observations (not counted)

1. **SWDIO F.Cu (12.6, 36.1)–(18.5, 35.45): a new local_bump_review instance.**
   - The window is 8.221 mm; a 7.700 mm redraw clears RedrawCheck.
   - It appears because the chamfer gave the window a fourth heading.
   - The net is noncritical, so this is review-only. The final list needs to count it (the round 24 triage already called that list not yet due).
2. **USB_FAULT_N's local bump** lies inside the U-turn the detour table already discloses.
3. **J440.3 / .4 have AUX wire copper on both outer layers, and the GND via is 4.03 mm away.**
   - The B.Cu side is only the clamp stub.
   - route_check and M2 define a layer change through vias, so the triage's verdict stands. D-R19-15 is the context the triage did not cite.
4. **Information counts against `5516eeec…`:**
   - pad_end_offcentre 57 → 70; segment_inside_pad 22 → 27; short_layer_hop 8 → 18 (mostly the named barrels); extra_bends 8 → 14; local_bump_review 0 → 2.
   - Section 6 still gives older counts, scoped to their boards.
5. **Four T junctions sit within 0.08 mm of a segment end.** Two are inside pads; the VBUS and BUZZ_G ones were triaged in round 24.
6. **Two segments are exactly at the short-segment bound, not under it:** the PORT_4V8 U401 link halves at 0.25 mm and the GND C82.2 fan-out at 0.40 mm.
7. **Tightest partner vias:** PYRO1_GATE 1.492, SD_SCK 1.432 and PYRO1_OUT 1.421 mm.
8. **PYRO1_OUT's via has no In2 copper within 1.0 mm.** This is its S-8 void, excused by K-region.
9. **BAT_IN has a 0.141 mm diagonal wholly inside R167.1.**

## Coverage limits

- The pre-chamfer intermediate board was not rebuilt.
- IPC-2152 sizing, S-8 and pours were left to their gates and lenses.
- No DRC was run; the board is unchanged since the fix pass, which reported DRC 0.
