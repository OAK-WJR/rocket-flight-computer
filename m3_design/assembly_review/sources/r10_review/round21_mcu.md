# R10 round 21: MCU lens (Claude)

- Target commit `accfff4947266a23cf60a63f3d92be047f5391b5`.
- Board SHA-256 before and after: `0dc847761de94a45cf68b1c82ec91f38e9d4ebb7297abc7108e3df9a454940d3` (unchanged).
- **Totals: 0 Critical, 0 Major, 1 Minor.** Machine-readable version: `round21_mcu.json`.

## Findings

| ID | Sev | Title | Key evidence |
|---|---|---|---|
| R21-MCU-01 | Minor | R10_VALIDATION calls the port TX ≤ 3.6 V rule "binding note obligation 15". | Line 1996. The binding note's obligations carry no numbers. Counted from 1, entry 15 is the TPS2553 FAULT obligation and the 3.6 V rule is entry 16. Text only. |

## What the polish pass changed at U1

- **Only U1.74's pour setting.** U1.74's zone connection went from inherited to none. Nets and positions of all 100 U1 pads are otherwise identical to `50a39de5…`.
- **No pad net changed anywhere on the board.** All 666 pad nets are identical. Only D440, D441 and TP82 moved.
- **No U1 net's tracks changed.** The track and via diff touches only AUX_*_WIRE, GND, USB_LIMITED and PORT_4V8.
- **U1.74 is still on GND through its own copper.** It has a 0.2 mm F.Cu stub, (17.5,35.45) → (17.5,39.3), to a GND via (drill 0.3 mm, pad 0.5 mm). That via sits inside the filled F.Cu, B.Cu and In1 GND pours.
- **The removed piece did nothing electrically.** It was a 0.2822 mm² F.Cu island with no via, bounding box (17.10,34.20)–(17.90,34.76), touching only pad 74. It is gone now.
- **Pin 75's decoupling path is unchanged.** C17 still returns through the same via.

## Checks

**Netlists and records**
- A fresh kicad-cli 10.0.7 schematic netlist matches the board and the committed `schematic.net.xml` on 666 / 666 pins.
- DRC with schematic parity gives 0 violations, 0 unconnected and 0 parity issues.
- `pin_table.tsv` `r10_net` matches the board on 100 / 100 pins, and so do the binding note's `u1_pins`.
- The binding note's board, netlist, pin_table and circuit hashes match the files.
- None of the 32 no-net pads has any copper.

**DS12110 Rev 8 pin and AF checks**
- The pin names match pin_table (Table 9 for 97 pins; the LQFP100 pinout figure for pins 17–20).
- PD8 / PD9 are AF7 USART3 (Table 13, continuation page, p94).
- PC6 / PC7 are AF7 USART6 (Table 12 p92).
- PB12 / PB13 are AF14 UART5 (Table 11 p91).
- All three ports wire TX to pin 3 and RX to pin 4 of their connector.
- PC1 is FT_ha with RTC_TAMP3/WKUP5, as obligation 7 says.

**Port enable, port rules and VREFBUF**
- **PA4 port-UART enable rule.** U11.9 ST is pulled up by R91 (10 kΩ, inside TI's 6–20 kΩ band). IN2 is RAW_PROTECTED. TPS2121 SLVSEA3F Table 9-3 p18 says ST is low only while IN2 powers the output. The rule appears for PD8, PB13 and PC6.
- **TX ≤ 3.6 V and unmapped-port rules.** They are in binding obligations 16 and 3, ORDERING §8, M3_R10 and parts_qualification.
- **VREFBUF.** Obligation 36 now forbids any write to VREFBUF_CSR. VREF+ and VDDA are both on 3V3A through R164. R164 is 2.2 Ω: LCSC C22939 is 0603WAF220KT5E, 2.2 Ω 1 %.

**Gate networks and IMU**
- **Q122 (PC1).** R122 1 kΩ series, R123 2 kΩ pull-down and C123 10 nF all sit on ACT_EN.
- **Q124 (PE4).** R126 220 Ω series, R127 1 kΩ pull-down at the pin, R128 10 kΩ and C126 220 nF gate–source: AGENTS §2.4 is met.
- **IMU_INT1.** It joins only U1.98 (PE1) and U4.4. The ISM6HG256X datasheet gives INT1's default as "output forced to ground". U4 sits at B(17,45.9), rotation 180, so the lever arm is x = −6.0 mm, which matches the binding note.

## Fix verification

| Item | Verdict |
|---|---|
| D-R20-03 (U1.74) | Confirmed |
| D-R20-02 (MCU side: GPS_RX_MCU unchanged) | Confirmed |
| D-R20-09 (MCU side unchanged) | Confirmed |
| D-R19-14 (port UARTs) | Confirmed |
| R19-MCU-01 (PA4 rule) | Confirmed |
| R20-MCU-01 / R19-MCU-04 (VREFBUF) | Confirmed in the records (still an Inference: RM0433 not retrieved) |
| R20-MCU-02 / -03 / -04 | Confirmed, with the pointer defect R21-MCU-01 |
| D-R19-04 (Q122 gate network) | Confirmed |
| D-R19-11 (IMU_INT1) | Confirmed |
| D-R19-05 (U1.19) | Confirmed |

## Fix now

- **R21-MCU-01 (text only):** at R10_VALIDATION line 1996, cite the obligation by its content ("On VLOGIC undervoltage/shutdown …") instead of the number 15.

## Coverage limits

- RM0433 and AN5690 downloads timed out, so the VREFBUF mode table remains an Inference, as recorded.
- AN2606 was not re-read.
- No firmware exists and nothing was measured on hardware.
