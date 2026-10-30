# Round13 routing fix receipt

Routing sources are frozen. Twelve predefined signal cleanups remove **6.175186069 mm and seven segments**. The isolated combined candidate has 209 footprints, 966 segments, 296 vias and 1802.125220178 mm of track. Only `m3_design/r10_route_signals.py` and `m3_design/r10_route_usb.py` were edited.

Base commit `fa897c81abac3026e75ca5cc88bef0c2659a7130`; canonical PCB before/after this worker source phase remained `7355ae1aeb1fdfdf6f64317945a0bf114d94c2bb65fb04adfbcd5a2b8037b09c`. No canonical CAD save occurred. Root owns subsequent integration; candidate hash is `a6a225280dc13a818fed8ac5605564a008d53e6f7f765cf717412d6b772e173b`. The original Round13 reports remain immutable.

| Net | Changed segments | Native length removed (mm) | Native replacement (mm) | Reduction (mm) |
|---|---:|---:|---:|---:|
| CAM_RX_BUFFER | 4 → 2 | 7.651344597 | 6.494416675 | 1.156927921 |
| LED_YEL | 3 → 3 | 4.200065916 | 3.172792206 | 1.027273710 |
| BUZZ_DRV | 4 → 2 | 6.538477631 | 6.304163056 | 0.234314575 |
| V3V3_SENSE | 4 → 2 | 4.393208512 | 4.128111832 | 0.265096680 |
| LOGIC_SOURCE_ST | 3 → 2 | 5.044417382 | 5.044417382 | 0.000000000 |
| RADIO_TX_MCU | 3 → 2 | 8.168376618 | 8.168376618 | 0.000000000 |
| VBUS_SENSE | 4 → 2 | 11.796803743 | 10.170458146 | 1.626345597 |
| CAM_PWR_EN | 2 → 3 | 5.525000000 | 4.631675683 | 0.893324317 |
| CAM_FAULT_N | 2 → 3 | 2.230000000 | 2.036690476 | 0.193309524 |
| GPS_TX_WIRE | 2 → 3 | 3.125000000 | 2.788172798 | 0.336827202 |
| GPS_RX_WIRE | 2 → 3 | 3.225000000 | 2.888172798 | 0.336827202 |
| NRST | 4 → 3 | 11.144995667 | 11.040056326 | 0.104939342 |

These are measured changed windows; unchanged portions of each net are excluded. All old window segments match the native source board at 0 nm. Final source dry runs reproduce precisely the combined native segment delta. Exact adopted polylines and source hashes are retained in [the JSON receipt](round13_routing_fix.json). Equal-length LOGIC_SOURCE_ST and RADIO_TX_MCU changes remove one segment each. All 12 options pass; no disqualified sketch was adopted.

All 12 individual candidates pass 15 native reference/hygiene/safety geometry rules and route topology checks, then genuine official KiCad 10.0.7 all-severity/schematic-parity DRC. The combined candidate additionally passes 16 selected rules including F9-2, full critical bump auditing and the supplementary all-net adversary. Native DRC exits 0 with 0 violations, 0 unconnected items, 0 parity errors and 0 ignored checks. Critical audit searches 25 windows and the all-net audit 54 windows; both find 0 bumps. Production rules and search limits are unchanged.

The LED_YEL vertical leg `(14.4,43.0) → (14.4,43.7)` approaches U1.89/SPI1_SCK at a native collision threshold of 0.150000–0.150001 mm. This satisfies the 0.15 mm floor with no extra search reserve. Production redraw exploration retains its 0.16 mm reserve; this result does not prove global routing optimality.

Native invariants compare every pad/net, footprint/pose, via/net/fill/cap, zone outline/rule/net and outline edge identically. Tracks on every net outside the 12-net list compare exactly; changed tracks retain 0.2 mm width and original outer copper layers. No power/GND/pyro/HSE/QSPI/SPI/SD/IMU path, via, layer change, circuit or support was changed. Only saved zone fills vary through native refill.

Current production inventory is **140 = 110 ordinary information + 22 inside-pad representations + 8 noncritical hygiene leftovers**. The V3V3_SENSE tiny-jog instance is gone. There are 57 off-centre entries, four between-pad routes (C84/3V3 F 0.540007 mm; C22/BAT_FAULT_N B 0.200041; C28/USB_FAULT_N B 0.200041; R87/RAW_ACT B 0.275038 mm), five literal near-edge endpoint instances (L1.2 once; R432.1 twice at 0.020 mm polygon depth; R120.2 twice), and three short layer-hop information items. Fresh AUD-2 diagnostics give 11 split/void observations: 5 runs, 5 pads and 1 connected chain. These are not 11 nets or new blocking requirements.

The eight remaining noncritical leftovers are counted and located once in JSON. No per-instance measured metadata or stale-coordinate requirement is introduced. Supplementary candidate searches are excluded from the 140 production instances. NRST/BOOT0/I2C return-companion distances and the 0.05 mm U4.14 MOSI offset remain inherited M2 deviations.

R13-RTE-01 is fixed in source and isolated CAD pending canonical integration. R13-RTE-02/03 remain carried Minor geometry groups. This receipt supplies no new Critical/Major and does not replace the original full-review totals or acceptance reviews. No physical or firmware test is claimed.

CLI reservation was released after the combined DRC. No source edit remains pending. Root must complete two native integration builds, the full gate/tests, hash provenance and fabrication refresh.
