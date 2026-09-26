# M3-ASSY-R2 — merging servos, pyro, arming, pull-pin and buzzer into the single board

Status: **design + CAD only.** Nothing in this document has been measured on a real board. Every value below is either taken from a named datasheet / LCSC page (URL given), taken from an earlier ruling in this repository (section given), or marked **inference**.

## 1. Vehicle-level decisions this revision is built on (owner rulings, 2026-09-25)

| Decision | Ruling | Consequence on the board |
|---|---|---|
| Deployment mode (`FMEA_REDUNDANCY.md` §3.2 open item) | **Single deploy.** Both on-board channels are apogee channels; ch2 fires unconditionally 2.0 s after ch1 is commanded. Redundancy is wanted **on this board** and, independently, from a commercial altimeter | Two fully independent pyro channels, each with its own fused bus (FMEA H-5 adopted), its own arm sense, its own continuity sense |
| Backup altimeter interface (`STATUS.md` "undecided") | **None — fully isolated.** The commercial altimeter has its own battery, switch, igniter and charge; it shares no copper, ground, harness or connector with this board | Nothing on the board. Recorded here so it is not "quietly added" later |
| Scope of this revision | Design + manufacturing package, no order placed | BOM / CPL / Gerber generated; no quote accepted, nothing purchased |

## 2. What was added (5 new schematic sheets, one per function)

### 2.1 Sheet 11 — actuator power switch (`actuator_power.kicad_sch`)

The existing M3 battery path (U9 TPS259470L eFuse) is **explicitly not sized for servo or pyro current** (its own schematic note: "Power rail serves core/camera, not servo motor current"). A second, high-current path is therefore added, taken from `BAT_IN` next to J1 (the frozen M1 topology, `reference/m1_power_actuator/m1.py`):

- **Q120 / Q121 AON6403** (LCSC C2760089, as frozen `ROCKET_FC_FROZEN_DESIGN.md` §4.3) back-to-back common-source P-FETs: load switch + reverse-battery block + no back-feed from `RAW_ACT` into `BAT_IN`.
- Gate network: R120 100k gate→common source, **C120 2.2 µF gate→common source** (`MARGIN_PRESCRIPTION.md` P0-4; gate-*source*, never gate-ground, so a shorted capacitor fails *off*), R121 10k to the driver.
- **Driver Q122 AO3400A**, gate from `RAW_PROTECTED` through R122/R123 100k/100k. Consequence: the actuator rail is on **only when the U9 logic path is on**, i.e. it follows the same single external switch contact (J1.3–J1.4) and U9's fault latch. There is still exactly one power switch on the vehicle. On USB power alone `RAW_PROTECTED = 0`, so the servo header and the arming terminal are dead — the "USB first, battery second" bring-up rule of `DESIGN_ASSURANCE.md` keeps working.
- **C121 470 µF / 25 V polymer** (C46550466) on `RAW_ACT` — the servo/pyro bulk.
- **RAW_ACT sense R124/R125 10k/4.7k + C122 10 nF → PB0** (ADC12_INP9, FT_a). The 14.7 kΩ load is also the bleed that `CIRCUIT_REVIEW.md` §2.8 asks for: τ ≈ 14.7 kΩ × ~490 µF ≈ 7 s instead of 72 s.
- Off-board, mandatory (unchanged from `MARGIN_PRESCRIPTION.md` P0-3): **in-line 15 A ATO blade fuse in the battery lead.** There is no on-board fuse ahead of Q120.

Operating point (inference from datasheet typicals, not measured): Vgs(Q120/121) = −BAT × 100k/110k = −7.6 V at 8.4 V, −5.5 V at 6.0 V; AON6403 Rds(on) ≤ 4.3 mΩ at −4.5 V (datasheet), so the switch pair drops < 70 mV at 7.66 A.

### 2.2 Sheet 12 — pyro channels, arming and continuity (`pyro.kicad_sch`)

Two identical channels. Per channel *n* (1, 2):

| Function | Parts | Source of the value |
|---|---|---|
| Low-side switch | **AON7524** (C431195), DFN3x3A EP, drain = paddle | `MARGIN_PRESCRIPTION.md` P0-2 (AO3400A thermally over-stressed; AON7524 guarantees 5.8 mΩ at Vgs 2.5 V, EAS 20 mJ, 100 % UIS tested) |
| Gate network | 220 R 0805 series (C17557), **1 k pull-down on the MCU side** (C11702), 10 k gate→source (C25744), **220 nF gate→source** (C21120, 25 V X7R) | P0-1 + P0-2 item ① (220 nF required with AON7524, otherwise Qgd self-turn-on) |
| Continuity | 10 k / 1 k divider from the drain + 10 nF | frozen §5.2; filter cap from `CIRCUIT_REVIEW.md` §2.5 |
| Output bypass | 100 nF / 50 V X7R drain→GND at the terminal (C14663) | `CIRCUIT_REVIEW.md` §2.6 (ESD / RF on the igniter lead; slows the plug-insertion drain edge) |
| Cold pull-up | 47 k (C25792) from each drain to one cathode of **D120 BAT54A** (C8591), common anode = 3V3 | FMEA H-1 (turns "FET shorted" into a measurable state with the plug out) |
| Arm sense | 10 k / 1 k divider from **each** fused bus + 10 nF | frozen §5.2 + H-5 (one sense per bus, because the buses are now independent) |

**Arming (FMEA H-5 adopted, DESIGN_ASSURANCE "ARM on its own connector" adopted):**

- J120 **ARM terminal**, 4-pos DB128V on the right-hand long edge: `RAW_ACT / PYRO2_BUS / PYRO1_BUS / RAW_ACT`. The removable arming plug is a four-wire, two-fuse link: pin 4 → F1 (5 A **fast-acting**, P0-3a) → pin 3 (BUS1), pin 1 → F2 (5 A fast-acting) → pin 2 (BUS2). The middle order is chosen so each bus runs as one straight 2 mm strap to the igniter terminal on the opposite edge. With the plug out there is **no copper, part or test point** between `RAW_ACT` and either `PYRO*_BUS` (AGENTS.md safety rule 1; verified by the netlist gate in §4).
- J121 **igniter terminal**, 4-pos DB128V on the left-hand long edge: `PYRO1_OUT / PYRO1_BUS / PYRO2_BUS / PYRO2_OUT`. Igniter 1 across 1–2, igniter 2 across 3–4.
- Both pin orders are **reversal-symmetric**: a terminal wired counting from the wrong end still pairs RAW with a BUS (J120) and BUS with its own OUT (J121). With single deploy, swapping ch1/ch2 is harmless.
- A short on one igniter now blows only that channel's fuse; the other channel is untouched (V-5 closed). Residual common points, stated honestly: `RAW_ACT`, Q120/Q121, the battery and the MCU.

**Gate pins:** PYRO1 = PE4 (pin 3), PYRO2 = PE5 (pin 4) — the frozen choice (`DESIGN_ASSURANCE.md` recommends not re-deriving it). FMEA H-2's move of PYRO2 to PE13 is **rejected**: frozen §3.9/§3.10 list PE13 as a ROM-bootloader push-pull output (SPI4 MISO), forbidden for a pyro gate. Instead the two neighbours are made sentinels: **LED_RED moves from PE3 (pin 2) to PE8 (pin 38)**, so pins 2 (PE3) and 5 (PE6) carry no net and firmware drives them low permanently. A PE4–PE5 bridge fires both channels together, which under single deploy only removes the 2 s stagger (both charges are sized for simultaneous firing, FMEA §3.2).

ADC map: PYRO1_CONT = PC0 (pin 15, FT_a), PYRO2_CONT = PC1 (pin 16, FT_a), ARM1_SENSE = PC5 (pin 33, TT_a), ARM2_SENSE = PC4 (pin 32, TT_a). At the SMBJ9.0CA clamp on BAT_IN the TT nodes stay below 1.5 V (inference, 10k/1k ratio).

Not adopted, with reason: per-drain SMAJ18A (H-8, "SHOULD") — the AON7524 is avalanche-rated (EAS 20 mJ) and the TVS leakage would bias continuity; bus TVS (§2.6 optional) — deferred to bench evidence.

### 2.3 Sheet 13 — servo outputs (`servos.kicad_sch`)

- J122 3×4 straight header (C32713291), **column-major** (footprint pads 1/2/3 share one column): pins 1/4/7/10 = SERVO1..4_OUT, 2/5/8/11 = RAW_ACT, 3/6/9/12 = GND (M1 rev H + `CIRCUIT_REVIEW.md` §5(c)).
- MCU side → **10 k pull-down + SRV05-4 clamp channel → 1.0 k 0805 series** (C17513) → header. 1.0 k instead of 220 R per `MARGIN_PRESCRIPTION.md` P0-5 (220 R lets 36 mA into a driven-low GPIO in a chafe fault).
- D121 SRV05-4 (C13612): pins 1/3/4/6 = SERVO1..4_MCU, 2 = GND, 5 = 3V3 (Semtech pin configuration).
- 2 × 22 µF 0805 on RAW_ACT at the header.
- MCU: SERVO1..4 = PA0..PA3 (TIM5_CH1..4, AF2), frozen §3.2.
- Two Ø3.2 mm zip-tie holes straddle the header (`DESIGN_ASSURANCE.md` §5 item 4).

### 2.4 Sheet 14 — launch pull-pin and buzzer (`pullpin_buzzer.kicad_sch`)

- J123 1×2 header: `PULLPIN_EXT / GND`. 1 k series, 10 k pull-up to 3V3, 100 nF to GND (DESIGN_ASSURANCE C27), **D122 BAT54S clamp** to 3V3/GND on the MCU-side node (FMEA H-10: an 8.4 V chafe would otherwise put 7.94 V on the pin). → **PC14** (pin 8), changed from the frozen PD14 so the signal leaves the MCU on the side facing the actuator band. PC14 sits in the backup domain (low drive, 2 MHz); it is used only as an input, and with the BAT54S clamp the node cannot exceed ≈3.7 V, so the FT_h argument that selected PD14 is no longer needed. PC13 (pin 7, CAM_UART_OE) is its neighbour; a bridge there only corrupts an advisory input.
- Buzzer LS120 MLT-8530 (C94599): pad 1 = + lead = 3V3, pad 2 = − lead = BUZZ_OUT, pads 3/4 = dummy. **Resolves `CIRCUIT_REVIEW.md` §3.4**: the Huaneng specification (dated 5/22/2017, <https://files.seeedstudio.com/products/107020109/document/MLT_8530_datasheet.pdf>, §5.2 soldering pattern) shows "+ Lead" and "− Lead" on the **same** edge and both dummy pads on the sound-port edge; the library footprint has pads 1 and 2 on one edge. Rated 3.6 V₀₋ₚ, 95 mA max, 16 Ω, −20…+70 °C.
- Q123 AO3400A low side, D123 1N5819WS freewheel (pad 1 = cathode = 3V3), 220 R gate resistor + 10 k pull-down.
- BUZZ drive = **PA5** (pin 29) — moved off PE6 per `MARGIN_PRESCRIPTION.md` P1-10 (not adjacent to any pyro gate or to I2C1). PA5 is a ROM-bootloader SPI1 *input* (frozen §3.10), so the buzzer stays silent in DFU. TIM2 must still never get a channel (frozen §3.2); use a software toggle or TIM8_CH1N (AF3 — an **inference** from the AF table, to be checked before firmware relies on it).

## 2.5 Board geometry and routing

- The board grows from 186 mm to **238 mm**: a 52 mm actuator band is inserted at y = 34 mm, between the battery/logic-power block and the camera block. Every existing part, track, via, pour and hole below y = 34 moved down by exactly 52 mm; the seven tracks that crossed the cut (BAT_FAULT_N, USB_FAULT_N, 3V3, VBUS, LOGIC_SOURCE_ST, RAW_PROTECTED, VLOGIC) continue through the band as straight B.Cu lanes.
- Band layout: actuator switch at the top (y 34–47), ARM terminal on the right edge and igniter terminal on the left edge with both pyro stages between them (y 47–70), servo header on the centreline with the buzzer left and the pull-pin right (y 70–86). All high current stays inside this band, next to the battery entry (`HISTORY.md` §2).
- Hand-defined high-current copper: BAT_IN on In2 (J1.1 → Q120, 12 × 0.35 mm vias) and an F.Cu strap per drain pin; ACT_FET_S and RAW_ACT F.Cu pours (6–7 mm wide on the right-hand strip); 2.0 mm BUS straps; 2.4 mm igniter-return straps; source straps with two GND vias per pyro FET into the In1 plane; one straight 0.3 mm gate line per channel (FET gate → 10 k → 220 nF → 220 R → test pad).
- Servo feed: RAW_ACT reaches the header's + column through a 2.6 mm F.Cu neck and a 2.8 mm finger; the four + pins are joined by a 2.4 mm strap. With all four MKS HV6120 stalled (7.66 A, GEOMETRY_REV_G) the neck is at roughly its IPC-2221 20 °C-rise limit — an **inference** from the standard's external-layer formula, not a measurement.
- Signal and small-power nets inside the band were routed with Freerouting 2.4.1 (all pre-existing copper locked, In1 declared a power layer so the ground plane stays unbroken, 0.2 mm clearance). Freerouting ignores pours, so its copper was kept only inside the band; every connection from the band to U1, and a few in-band fix-ups, were routed with a small grid router that treats the 3V3 / 3V3A / VLOGIC pours as obstacles (0.16 mm clearance, no via-in-pad). Like the R1 support nets these are constraint-searched, not hand-optimised.
- To reach U1 the MCU-bound signals use In2 only inside a documented channel of the 3V3 plane (x 8.2–16 mm, y 124–167 mm, plus a pocket x 16–18.2 mm, y 150.5–157.6 mm). The region was chosen because no 3V3/3V3A via there depends on the plane; the plane stays one connected piece (checked by DRC: 0 unconnected items). R1's CAM_PWR_EN and CAM_FAULT_N B.Cu routes under U1's top-left pins were re-routed to free that escape.
- GND: outer-layer pour pieces without a via got fan-out/stitching vias into the In1 plane; every GND pour piece is connected (DRC).
- Silkscreen: references are 1.0 mm (the board's minimum). Where no legal top-side spot exists in the dense pyro/servo cells, the reference is on the bare bottom side, mirrored, at the same location. Bottom silkscreen also carries the terminal pin names (RAW/BUS2/BUS1/RAW, E2−/E2+/E1+/E1−, S + −, PULL/GND) and the arming note.
- Two Ø3.2 mm zip-tie holes straddle J122.

## 3. Datasheet evidence for new footprints / pinouts

| Part | Evidence | URL |
|---|---|---|
| AON7524 pinout (1-3 S, 4 G, 5-8 D + paddle) | AOS datasheet Rev 1.1 Oct 2023, p.1 | <https://www.aosmd.com/res/datasheets/AON7524.pdf> |
| AON7524 land pattern | AOS package outline **DFN3x3A_8L_EP1_P, PO-00047 rev I** (the outline named on the AON7524 product page; note: DFN3.3x3.3_8L_EP1_S / PO-00093 is a *different* package) | <https://www.aosmd.com/sites/default/files/res/packaging_information/DFN3x3A_8L_EP1_P.pdf> |
| AON7524 LCSC | C431195, AOS, DFN-8(3x3), 14,170 in stock on 2026-09-25 | <https://www.lcsc.com/product-detail/C431195.html> |
| BAT54A / BAT54S pinout | Vishay doc 86410 rev 1.1: BAT54A pins 1,2 = cathodes, 3 = common anode; BAT54S pin 1 = A1, 3 = K1/A2, 2 = K2 | <https://www.vishay.com/docs/86410/bat54_bat54a_bat54c_bat54s.pdf> |
| BAT54A LCSC | C8591 (JSCJ BAT54A) | <https://www.lcsc.com/product-detail/C8591.html> |
| BAT54S LCSC | C47546 (Nexperia BAT54S,215) | <https://datasheet.lcsc.com/lcsc/1811141220_Nexperia-BAT54S-215_C47546.pdf> |
| SRV05-4 pinout | 1/3/4/6 I/O, 2 GND, 5 VCC | <https://www.onsemi.com/download/data-sheet/pdf/srv05-4-d.pdf> |
| 220 nF 0603 | C21120 = Samsung CL10B224KA8NNNC, 25 V X7R | <https://www.lcsc.com/product-detail/C21120.html> |
| 100 nF 0603 50 V | C14663 = YAGEO CC0603KRX7R9BB104 | <https://www.lcsc.com/product-detail/C14663.html> |
| 1.0 k 0805 | C17513 = UNI-ROYAL 0805W8F1001T5E | <https://www.lcsc.com/product-detail/C17513.html> |
| MLT-8530 pads | Huaneng spec §5.2 (see §2.4) | as above |
| TXU0202DCUR (existing U12) | LCSC code was empty in R1 and would have blocked JLC assembly; C5186957 = TI TXU0202DCUR, VSSOP-8, 16,760 in stock 2026-09-25 | <https://www.lcsc.com/product-detail/C5186957.html> |

## 4. Evidence and what still has to be verified before a fab release

Done (CAD only, 2026-09-25, KiCad 10.0.6):
- `tools/check.sh`: DRC 0, unconnected 0, schematic parity 0, ERC 0; metadata / 3D-model audit OK.
- `quality_audit/verify_board.py` with zone refill: PASS.
- `m3_design/check_actuators.py`: the arming break, both gate networks, sentinels, drain membership, servo chain, load-switch gating, buzzer pad mapping and pull-pin clamp, read from the PCB's own pad nets: OK. Negative tests (one bus pad moved to RAW_ACT; a net on the PE3 sentinel) are rejected.
- Manufacturing package regenerated by `python3 tools/export_fab.py` (Gerber/drill zip is git-ignored; BOM and CPL are committed).

Not done — must happen before anything is ordered or flown:
- Real-board power-up of the actuator switch (turn-on time with C120, inrush into C121, U9 interaction when `RAW_PROTECTED` sags during a servo stall) and a thermal check of the servo feed under stall.
- Fire tests into a 1 Ω dummy load on each channel, with the plug-insertion (Miller) test of `DESIGN_ASSURANCE.md` repeated 20× per channel.
- Cold pull-up four-state table (FMEA H-1) measured on the bench; the table in FMEA assumes a single shared bus and must be recomputed for the split buses.
- Firmware for servo / pyro / pull-pin / buzzer does not exist; v0.8.1 is bound to R1 and must not run on R2.
- JLC review of CPL rotations, the THT parts (terminals, headers) as hand-solder or THT service, and sourcing for R9 / R84 / R86 (no LCSC code, unchanged from R1).
- Mechanical: the board is now 238 mm long; sled, bay length, harness exits and the plugged-servo-header height budget (GEOMETRY_REV_G §7) must be re-checked for this length.
