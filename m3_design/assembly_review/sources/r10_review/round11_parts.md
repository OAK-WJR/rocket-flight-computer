# Round 11: parts, BOM, lands, supplier stock and orientation

Target: commit `21bc3b2`, native PCB SHA-256
`0c50b9fd0930f34edab7129fc21b8e71d0ee03bc079e1900b7e131cece6bfaf8`.
Read-only review; no CAD, generator or fabrication output was edited; no other current-round lens report was read.
Evidence: [round11_parts.json](round11_parts.json). Root owns the fresh complete gate.

**New findings: 0 Critical, 1 Major candidate, 1 Minor.** The Major needs the coordinator's
fresh verification. Existing land/process/stock obligations below are not counted as new Majors.

## R11-BOM-01 — Major candidate: DB125 maximum wire face exceeds the passing model

`m3_design/r10_parts.py:149–152` gives every DB125 local depth `−4.05…+3.65 mm`.
The [DORABO T0-1 drawing, sheet 1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf)
dimensions total depth `7.40 mm` and pin-row-to-rear `3.90 mm`; its general tolerances are
respectively `±0.30` and `±0.20 mm`. Thus the allowed wire face reaches
`+(7.70−3.70)=+4.00 mm`, 0.35 mm beyond the model. No dimensional correlation narrowing
that corner is supplied. This is a drawing-based tolerance calculation, not a measured part.

All seven native terminals consequently have drawing-corner wire room
`sqrt(25.4²−5²)−20−0.3 = 4.603012 mm`, versus model `4.953012 mm` and the
owner-accepted **4.95 mm P-11 floor** (`tools/check_r10.py:1882–1903`). West entry faces
can reach x=3.00 rather than 3.35; east faces x=43.00 rather than 42.65. This fails an
explicit accepted CAD bound; it is not an assertion that the unbuilt harness physically collides.

The same drawing shows an interlock tab at the local −x end beside pin 1. The 2P models
omit it; 4/5P models give extra overall span but do not fully bound its asymmetric position
and tolerance. Directly using right-end `1.75±0.20`, length `N×3.5` (±0.30 for 2P,
±0.50 for 4/5P) and tab `0.42±0.20` gives the following conservative local tolerance unions:

| Variant | x union, mm | y union, mm | z, mm | Corresponding model centre/size (cx,cy,sx,sy) |
|---|---|---|---|---|
| 2P GN/BK | −4.62…+3.70 | −4.10…+4.00 | 0…8.90 | −0.46, −0.05, 8.32, 8.10 |
| 4P GN | −8.32…+7.20 | same | same | −0.56, −0.05, 15.52, 8.10 |
| 5P GN | −10.07…+8.95 | same | same | −0.56, −0.05, 19.02, 8.10 |

These are tolerance unions across permitted dimensional corners, not the dimensions of
one part. The tab faces −y on west terminals and +y on east terminals. Current courtyard
centre-line extents also underbound these unions: 2P local x≈±3.9, 4P≈±7.75, 5P≈±9.5,
all ending at y≈+3.9. Lands/drills/pin numbering need no change to correct the envelopes.

Native neighbour measurements with those unions, all in mm:

| Terminal centre | Nearest top body / gap | Nearest support / body distance | Locked J430 xy / 3D gap |
|---|---|---|---|
| J1 (7,75.85) | C80 / 1.300 | (3.7,86) / 6.450 | 37.892 / 37.926 |
| J121 (7,55.85) | Q124 / 1.000 | (4,44.3) / 6.930 | 18.401 / 18.471 |
| J400 (7,65.85) | R165,R80 / 1.100 | (3.7,86) / 16.450 | 28.057 / 28.103 |
| J410 (39,15.5) | J420 / 0.480 | (42,4) / 4.300 | 3.900 / 4.215 |
| J420 (39,31.5) | J410,J9 / 0.480 | (42,4) / 20.300 | 3.900 / 4.215 |
| J9 (39,47.5) | C60 / 0.3299 | (42,86) / 30.180 | 7.580 / 7.747 |
| J122 (39,71.5) | R431 / 2.150 | (42,86) / 4.430 | 29.013 / 29.057 |

No top-body overlap or 3.8 mm support violation was found; minimum radial bore margin
remains 2.61256 mm. The problem is the wire-room claim and incomplete envelopes.

**Concrete fix:** correct the four R10 DB125 generated model boxes and their R10 courtyard
graphics using the actual pin datum and tab, then restore ≥4.95 mm wire room. Moving each
terminal at least 0.35 mm inboard restores the original modelled room, but that is not a
complete legal placement by itself: J9's conservative C60 gap would become −0.0201 mm.
Re-place that local neighbour as needed, regenerate from source, and re-run fit, native
DRC, P-11, actual-feed hot-plug extraction, binding/fab and reproducibility. Alternatively,
obtain maker tolerances proving a smaller face envelope; do not silently lower P-11.

## R11-BOM-02 — Minor: current camera qualification reverses board directions

`sources/r10_design/parts_qualification.md:116` calls J9.3 `CAM_RX_WIRE(boardTX)` and
J9.4 `CAM_TX_WIRE(boardRX)`. Native schematic/PCB and printed RXI/TXO legends are correct:

- J9.3 at (39,45.75) → R100 → U12.1 B2 → U12.4 A2Y → U1.37 UART7_RX.
- U1.38 UART7_TX → U12.5 A1 → U12.8 B1Y → R101 → J9.4 at (39,42.25).

[TI TXU0202 SCES942A, p4 Table 6-1](https://www.ti.com/lit/ds/symlink/txu0202.pdf)
confirms those fixed directions. **Fix only the current record:** pin 3 is boardRX;
pin 4 is boardTX. Preserve the native circuit and F10 convention.

## Complete population, identity and export checks

- 209 native footprints = 209 XML components: 199 fitted LCSC parts plus J2 and nine test pads.
  All 199 appear once in the 82-code BOM and 199-row CPL. No identity/population discrepancy.
- All 651 unique numbered pin/net mappings agree between native PCB and XML, including
  repeated physical pad entries (663 total). Every native pad centre/size/drill/shape type
  matches its local library definition across 46 footprint names (44 fitted types).
- All 82 exact public supplier models equal the BOM Manufacturer Part strings; PCB/XML
  LCSC, Manufacturer and Manufacturer Part fields agree. No substitution was inferred.
- Fresh `jlc_orient.py --out` to local scratch: CHECK none. Independent CPL reconstruction:
  66 top +121 bottom rows, 12 nonpolar placement-only checks, 199 expected, zero errors;
  largest supplier pad-centre residual 0.491 mm. Current five-output manifest verifies.
- Fresh official JLCEDA pad maps for C466970/C52993880/C2757925/C3646874, C164170,
  C431196 and C5186957 have exactly the frozen heads and pad strings. Sources and fetch
  time are in the JSON; these are supplier-library checks, not a factory preview.

Every DB125 was checked, including its outward local +y entry, code, land and actual nets:

| Ref / role | Exact part / code | Native rotation / CPL | Pin roles in order |
|---|---|---|---|
| J1 battery | DB125-3.5-2P-GN-S / C466970 | −90 /270 | BAT_IN,GND |
| J400 switch | same | −90 /270 | BAT_SW_SOURCE,BAT_SW_RETURN |
| J121 igniter | DB125-3.5-2P-BK-S / C52993880 | −90 /270 | PYRO1_OUT,PYRO1_IGN |
| J410 GPS | DB125-3.5-4P-GN-S / C2757925 | +90 /90 | 4V8,GND,boardTX,boardRX |
| J420 radio | same | +90 /90 | same |
| J9 camera | same | +90 /90 | CAM_5V,GND,boardRX,boardTX |
| J122 servos | DB125-3.5-5P-GN-S / C3646874 | +90 /90 | SERVO1–4_OUT,GND |

All use 3.5 mm pitch, 1.90 mm copper /1.30 mm finished drill; maker drawing recommends
1.20 mm holes for 0.50×0.85 mm pins. The 28–16 AWG clamp range and colours match exact
supplier identities. Symmetric pin rows alone do not prove factory body orientation;
preview and physical wire/screwdriver access remain required.

J430 is **Molex 472192001/C164170**, not a push-push socket. The full rendered
[SD-47219-001 Rev G sheet 1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf)
([identical maker drawing mirror used locally](https://cdn.promelec.ru/upload/items/2020/09/01/472192001_sd.pdf))
agrees with eight 0.80×1.50 mm signal lands on 1.10 mm pitch and four 1.45×2.00 mm shell
lands. Shell aliases G1/G2/G3/G4→12/9/10/11 all join GND. Native bottom (24,24.3),0°
has CPL (24,−25.85),Bottom,180° because the supplier origin differs by +1.55 mm locally;
all 12 reconstructed pads differ by ≤0.005 mm. Pin order is DAT2,CS,MOSI,3V3,SCK,GND,MISO,DAT1;
all five 10 kΩ data/CS pulls and 100 nF/22 µF local bypasses are fitted. The
[Molex product record](https://www.molex.com/en-us/products/part-detail/472192001)
confirms eight circuits, 0.5 A/contact and −20…85 °C. No mechanical detect contact is
invented. Closed card envelope remains an explicit inference; actual card/hinge retention
and insertion access are untested. The current order notes preserve its 0.10/0.12 mm,
100% stencil requirement.

## Other maker-land checks and carried obligations

- Q120/Q121: native AONR21357 maker land agrees with
  [AOS PO-00047 Rev I, p1](https://www.aosmd.com/sites/default/files/res/packaging_information/DFN3x3A_8L_EP1_P.pdf):
  0.65 mm pitch, 0.35×0.50 mm source/gate lands, distinct drain fingers and asymmetric
  common drain. Opposed bottom poses (13.5,73.6),0° and (13.5,68.6),180° give CPL180/0;
  source/gate/drain identity and fresh supplier map agree.
- U401: DSK0010A numbered land and pad11 agree with
  [TI TPS7A91 SBVS282A, p3 and package pp35–36](https://www.ti.com/lit/ds/symlink/tps7a91.pdf):
  0.5 mm pitch, 0.60×0.25 mm fingers, 1.2×2.0 mm EP and split 1.13×0.89 mm paste.
  Only the two specified (27.3,13.6)/(27.9,13.6) VIPPO vias enter EP11. Filled/capped
  planar manufacture is an unverified order condition.
- **Carried Minor R4-BOM-01:** L400 at (24.2,5.55) still has 1.8×2.5 mm lands at ±2.35,
  versus [Bourns SRP5030T p1](https://www.bourns.com/docs/product-datasheets/srp5030t.pdf)
  recommended 2.0×1.8 at ±2.25 mm. The C189932 supplier proxy only establishes orientation.
  Keep the recorded assembly qualification or change to the maker land in a covered CAD pass.
- C84 remains exact MA25V470M8x10/C46550466, top (27.5,78.5),90°, positive pad1 VLOGIC
  at (27.5,81.75), CPL90°. Its derived land and missing reflow profile remain disclosed;
  manual fitting after both reflows and first-article polarity/ESR/capacitance checks remain
  necessary. No reflow qualification was inferred from the former OS-CON.
- Remaining inherited standard/passive/IC lands were included in the native-library,
  XML identity/pin-net, BOM and supplier/CPL walks. This lens did not freshly re-download
  a maker datasheet for every retained resistor/capacitor or establish physical solderability.

## Fresh exact-code supplier evidence

Public [JLC component-search API](https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList),
fetched **2026-10-30 00:15:29 UTC** (2026-10-29 local), all 82 exact codes returned:
46 Extended /36 Basic, no model mismatch, no thin lines. This is a read-only catalog
snapshot, not an accepted quote or order. Raw response SHA-256 and BOM/CPL hashes are
preserved in the JSON.

| Exact code | Stock | Required purchase for five boards | Result |
|---|---:|---:|---|
| C466970 green 2P | 35,696 | 10 | sufficient |
| C52993880 black 2P | 346 | 5 | sufficient |
| C2757925 green 4P | 37,865 | 15 | sufficient |
| C3646874 green 5P | 4,299 | 5 | sufficient |
| C164170 microSD | 8,716 | 5 | sufficient |
| C185349 R430 | 17 | **3,610** minimum | short |
| C26633007 U4 | 0 | 5 | short; stock/consignment required |
| C3662793 U9 | 101 | **7** minimum (five fitted) | sufficient; extra purchase cost |

Standard two-sided cost at five boards: parts **$57.52** + feeders **$25.092** =
**$82.61/board**, below the $84.41 placed-part/feeder target. Including supplier minimum
purchases, parts become **$59.86**, or **$84.95/board with feeders**, before $83.96/order
fixed fees, possible $14.93 handling, PCB, VIPPO/manual operations and shipping. R430's
minimum adds $1.8022/board and U9's extra two add $0.53784/board. Stock still fails M1.
Refresh within 24 h before ordering and resolve the exact quoted quantities/processes.

No DRC, simulation, firmware, bench, thermal, assembly-process, retention or physical-fit
pass is inferred from this parts review. The raw local supplier/probe artifacts remain in
`.supervisor/round11_parts_*`; the committed compact evidence is the linked JSON.
