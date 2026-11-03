# R10 round 29: routing lens (Claude)

- **Target:** commit `09a564e`, board `a0ec075e…`. SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and after.
- **Method:** read-only. Probes are in `.supervisor/r29_routing/`. Machine-readable copy: `round29_routing.json`.

## Totals

**0 Critical / 0 Major / 0 Minor real errors.**

## Findings

None. I applied AGENTS §3 and REQUIREMENTS M2 to the whole board with route_check and with my own scans. I also checked the routing figures the current docs quote. Nothing violates a rule, the gate catches every seeded defect, and no quoted figure is false.

## What was checked (observations, not counted)

**route_check (profile r10)**
- Gate mode on a probe copy: 0 failing, 0 allowlisted, 0 stale, 28 bump windows. The 5 unrecorded noncritical leftovers are BAT_OVLO, the BUZZ_DRV, BAT_FAULT_N and I2C1_SDA jogs, and the USB_ILIM detour.
- `--bumps-all`: pad_end_offcentre 70 and segment_inside_pad 27.
- On `92c3ad59…` the current tool fails exactly J440.3 (3.900 mm) and J440.4 (4.037 mm). Every other category count equals `a0ec075e…`'s.
- On `5516eeec…` it counts 59 right angles: F.Cu 25, B.Cu 31, In2 3. Of these, 53 are free and 6 are at a pad or via.

**45° rule and hygiene (own scans)**
- No arcs and no off-angle segments.
- 35 two-end 90° nodes. Each sits at a same-net pad or via whose copper covers the inner corner.
- 7 acute pairs. Each sits at a pad whose copper holds the wedge apex.
- Tiny jogs: only the recorded I2C1_SDA leftover.
- No free track ends. The six T joints land on a same-net track's centre line.

**GND partner vias and plated pins**
- 27 return-required layer changes: 25 vias plus J440.3 / J440.4. Each has a GND via 0.770–1.500 mm away.
- All 170 GND vias join the In1 GND fill.
- Plated pads with tracks on two layers: J440.3 / J440.4, J400.2 (AUD-2 slow) and J1.1 (power). Every other terminal pad has tracks on one layer.

**Reference planes**
- Under the 25 vias, In2 is 3V3 at 17 and PORT_4V8 at 4.
- HSE and PYRO1_GATE sit over In2 GND. PYRO1_OUT sits in its barrel void, with GND beyond it.
- J440.3 / J440.4 sit over In2 3V3.
- Nearest rail capacitors are 1.29–6.19 mm away, with 13 of the 21 beyond 4 mm. C460 is 16.28 / 15.86 mm from J440.3 / J440.4.
- Stack-up: B.Cu is 0.203 mm from In2 and 1.263 mm from In1.

**Doc figures reproduced**
- The detour table: 116 nets, 1500.8 / 1236.6 mm, 1.214×; all 23 rows and their via counts.
- The USB pair: 1.90 / 0.707 mm; the trunks are 16.448 / 14.702 mm.
- The contents row: 1059 segments, 309 vias and 1866.794 mm of track.
- In2 3V3: 1430.05 mm², 0.300 mm from the other rails.
- The R402.1 T: 0.075 mm inside the land.
- BAT_FAULT_N is 0.180 mm from a GND via.
- The D-R26 copper coordinates and clearances: 0.2005, 0.3865, 0.2338, 0.2062 and 0.9971 mm.
- A coordinate sweep of M3_R10, ORDERING §8, the handoff and R10_VALIDATION 2350–3031: every coordinate off the board is labelled as a "before" position or an older board.

**Gate seeds (probe copy)**
- Three seeds: J440.4's partner via removed, J440.3's partner via moved to 1.55 mm, and AUX_TX_WIRE's chamfer undone.
- route_check fails exactly these three: two critical_via_no_gnd and one right_angle.

**IPC-2152**
- tools/ipc2152.py widths are 0.680 / 0.356 / 0.326 / 0.299 / 0.167 / 0.157 mm for 2.9 / 2.0 / 1.9 / 1.81 / 1.294 / 1.249 A. Each is under its K-power floor.
- The 0.2 mm segments on power nets are sense, bypass, EN or second-barrel links.

## Fix verification

| Change | Verdict | Measurement |
|---|---|---|
| D-R28-01 … -04 | Confirmed, no routing effect | Board unchanged. route_check result identical. |
| Round 28 audit A item 11 and its siblings (J440 clamp distances in parts_qualification:36, M3_R10:97 / :132, R10_VALIDATION:1756 / :2046 / :2773, the D-R21-07 note, STATUS:21) | Confirmed | Along the track: 3.864 / 3.964 mm (2.59 + 0.509 + 0.765 / 0.865), each 0.211 mm shorter than 4.075 / 4.175. Straight centre to centre: 3.157 / 3.194 mm. Pad edge to pad edge: 1.865 / 1.900 mm. Earlier K-ports paths: J410 4.288 / 4.388 mm, J420 and J9 3.975 mm. J410 / J420 straight-line distances are 3.064–3.411 mm, which the docs round to "3.1–3.4". |
| Round 28 audit B, J440 partner vias | Confirmed | 0.300 mm from J440.3 / J440.4's pads. |

## Coverage limits

- Review-only M2 items were checked against the records, not judged one by one for removability. The final deviation list is not yet due.
- check_r10 was not run. K-ports, K-region and K-reference were reproduced by measurement instead.
- No DRC, signal-integrity or current-density solve.
- JLC hole-spacing limits were not re-read (manufacturing lens).
