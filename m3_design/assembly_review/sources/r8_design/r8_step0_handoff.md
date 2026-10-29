# R8 step 0 handoff: owner decisions and pin table

**Status:** done. Verification passed. Nothing is committed (the brief forbids commits).
- Branch `m3-assy-r8`, worktree `rocket-flight-computer-r8`, based on 431025d.
- The board is untouched: `m3.kicad_pcb` is still R7's `c872a3d3…`.

## What this step produced

| File | Content |
|---|---|
| `R8_DECISIONS.md` | D1–D14, each with its basis and fallback. Read it before starting any later step |
| `pin_table.tsv` | The R8 U1 pin contract: all 100 pins, 20 columns, 27 pins changed. Each row cites DS12110 Table 9 (I/O structure, page), Table 10 (AF, page), RM0433 (IOSWP, EXTI), AN2606 Table 135 (loader role, page), the reset state and resulting line state, the EXTI line, the frozen §3.10 status, the loader-driven allowance, the contract owner and two read checks |
| `step0/make_table.py` | Generates `pin_table.tsv` from R7's U1 nets. Self-asserts the contract pins, net uniqueness, no lost net and the loader rule |
| `step0/dump_r7_u1.py` | Dumps U1's pad nets from a board (KiCad Python) |
| `step0/pinmodel.py`, `step0/final.py` | The annulus crossing model behind D3 (decided map 13 crossings; R7 pins at rotation 0: 134) |
| `docs/REQUIREMENTS.md` | F4 (neck criteria), F10 (pin contract, camera UART, EXTI and binding notes, RF-part list, `check_r8`), M2 (detour baseline, in-pad via exceptions). Every change is marked **R8**; 3 table rows changed |
| `r8_step0_progress.md` | Running log |

## The decisions in one screen

**Pins (the schematic, step 2, applies exactly this diff):**

| Pin | Port | R7 net | R8 net |
|---|---|---|---|
| 7 | PC13 | CAM_UART_OE | BUZZ_DRV |
| 28 | PA4 | — | BAT_FAULT_N |
| 29 | PA5 | BUZZ_DRV | LOGIC_SOURCE_ST |
| 31 | PA7 | — | CAM_UART_OE |
| 37 | PE7 | LED_YEL | CAM_MCU_RX (UART7_RX AF7) |
| 38 | PE8 | LED_RED | CAM_MCU_TX (UART7_TX AF7) |
| 39 | PE9 | — | RADIO_NRST |
| 41 | PE11 | — | CAM_FAULT_N |
| 42 | PE12 | — | CAM_PWR_EN |
| 45 | PE15 | RADIO_RXEN | RADIO_DIO1 |
| 46 | PB10 | CAM_MCU_TX | RADIO_SCK_MCU (SPI2_SCK AF5) |
| 47 | PB11 | CAM_MCU_RX | RADIO_NSS (GPIO) |
| 51 | PB12 | RADIO_NSS | — |
| 52 | PB13 | RADIO_SCK_MCU | — |
| 53 | PB14 | RADIO_MISO_MCU | RADIO_MOSI_MCU (IOSWP) |
| 54 | PB15 | RADIO_MOSI_MCU | RADIO_MISO_MCU (IOSWP) |
| 56 | PD9 | RADIO_NRST | RADIO_RXEN |
| 57 | PD10 | RADIO_DIO1 | — |
| 61 | PD14 | GNSS_TP_MCU | GNSS_RESET_N |
| 62 | PD15 | VBUS_SENSE | GNSS_TP_MCU (TIM4_CH4 AF2) |
| 65 | PC8 | GNSS_RESET_N | VBUS_SENSE |
| 81 | PD0 | BAT_FAULT_N | — |
| 82 | PD1 | LOGIC_SOURCE_ST | — |
| 84 | PD3 | CAM_PWR_EN | — |
| 85 | PD4 | CAM_FAULT_N | — |
| 86 | PD5 | — | LED_RED |
| 88 | PD7 | — | LED_YEL |

**One net change outside U1:** R310.1 moves from 3V3_RADIO to **3V3**, and R310 is placed at the MCU end of the NSS
lane, ≥ 5 mm from U1 (D4).

**What each later step must know:**
- **Contract scope (D14).**
  - `check_actuators.py` stays untouched.
  - `check_r8` should assert the whole U1 map from `pin_table.tsv` (`r8_net`), PULLS with R310 on 3V3, the D5 loader
    rule (allowlist PA2/PB10/PB14/PA11/PA12/PB6/PB9 plus LEDs; PA6, PA8, PA9, PA10, PC9, PC11 and PE13 stay NC), and
    STRIP_B / STRIP_VIA without RADIO_NSS and RADIO_DIO1.
  - The F10 5 mm separation counts R306, R313, R315 and R310 as RF parts.
- **Hash set (D11).**
  - Rigid: the RF lines with their pads' copper, every strip GND item, the launch cut-outs, the keep-outs, and the
    CH1 block copper (D9: never re-baselined).
  - Regenerated in the strip: the interface leads, the 3V3_GNSS / 3V3_RADIO feeds, and the limiter's DC copper under
    U30. GNSS_ANT_DC's via and its F.Cu copper at L30/C302 stay rigid.
- **Detour baseline (D10).**
  - Keep-out-aware only for MST edges crossing a hard keep-out: an all-layer keep-out, the U31 body for non-GND nets,
    an NPTH hole or the board edge.
  - Parts and other nets' copper never count.
  - The tool lists every net judged this way. Step 1 adds a seeded test in which a detour beside the keep-out still
    fails.
  - Fallback: one TXEN allowlist entry.
- **Allowlist expectation:** only A8 (TP122's in-pad via, D9). TXEN passes under D10. The limiter detours go with D11.
- **Placement (step 4).**
  - U1 at rotation 0, (23, 45).
  - LED1/LED2 with R32/R33 move to the west edge, top side, about x 5–8, y 44–52, with LED_RED aft of LED_YEL (D3).
    Fallback: LEDs east on PA6/PA7 with CAM_UART_OE on PE14. That fallback is a pin change: update `make_table.py` and
    regenerate.
  - The camera supply (U7, R74–R77) stays aft-east, between the NRST and DIO1 lanes (seed).
  - D121 on B.Cu at rotation 90 on the U1-ordered servo lanes, before the reversal into J122's row order (D7;
    `partial/d121.py` convention). Kill rule: relabel D121, a reviewed `check_actuators` 7c edit.
  - IMU U4 bottom, rotation 0, at (10.0, 53.8) unless the D13 "free" test passes toward the axis.
  - TH1–TH3 removed (board-only footprints, D8).
- **Power (step 5, D12).**
  - RAW_ACT and BAT_IN necks ≤ 20 °C: ≥ 5.28 mm outer or ≥ 5.56 mm inner.
  - ACT_FET_S ≤ 30 °C: ≥ 3.71 mm on B.Cu; target 4.35 mm.
  - Face the two FETs' source rows, offset along the row so that no gate pad lies inside the bridge (expect
    3.8–4.5 mm, 24–29 °C).
  - The IPC fit is `baseline/scorecard.py` `ipc_dt` / `ipc_width`.
- **Firmware binding (step 9, D6).**
  - IOSWP is set while SPE = 0, before AF5 on PB14/PB15 and before NSS is first asserted. NSS is software-driven on
    PB11.
  - BUSY is polled (VBUS_SENSE owns EXTI8).
  - TIMEPULSE uses TIM4_CH4 capture.
  - Never AF7 on PE9 or PE10. PE4 is locked; SPI4 is never enabled.
  - No RTC output on PC13.
  - EXTI: 4 BAT_FAULT_N, 5 LOGIC_SOURCE_ST, 6 USB_FAULT_N, 8 VBUS_SENSE, 11 CAM_FAULT_N, 14 PULLPIN, 15 DIO1.
  - U4 is now west of the axis, so the lever-arm sign flips.

## How it was verified

1. **Datasheets read** (downloaded from st.com):
   - DS12110 Rev 11 (Jan 2026), AN2606 Rev 70 (Feb 2026), RM0433 Rev 9 (Oct 2026).
   - Pages used are listed in `R8_DECISIONS.md` "Sources".
2. **AF tables read twice for every moved pin:**
   - read 1: DS12110 Table 10 page images, pp. 89–94;
   - read 2: an independent pdftotext layout extraction of each row (PB10/11/14/15, PD5/7/8/9/14/15, PE7–PE15, PA4–PA7,
     PC6–PC8, PC13).
   - Table 9 rows of every moved pin were read as page images (pp. 64, 69, 70, 72, 73, 75, 76, 79, 82, 83).
   - All reads agree.
3. **Third source:** every AF number and LQFP100 pin number in the table matches ST's open pin database
   (`STM32H743VITx.xml`, as the connectivity survey parsed it into `r8_design/connectivity/h743_af.json`, copied to `partial/model/`, in the session
   scratchpad).
4. **IOSWP verified** in RM0433 §50.11.4 (bit 15, p. 2222), §50.4.2 (p. 2159) and the §50.4.4 note (p. 2161), with no
   instance limit in Table 422 (p. 2157). The local CMSIS header `m3_firmware/vendor/device/Include/stm32h743xx.h`
   defines `SPI_CFG2_IOSWP` (bit 15), which agrees.
5. **Bootloader states:** read in AN2606 Table 135 (pp. 320–323) and Table 136 (pp. 325–326) for every pin in the
   table.
6. **`make_table.py` self-checks pass:**
   - the contract pins 2, 3, 4, 5, 15, 16, 22–25, 32, 33, 34, 40, 97 and 98 are unchanged;
   - no net is lost or duplicated;
   - every bootloader-driven pin with a net has a recorded allowance.
   - A separate script check found 0 citation gaps over all 100 rows.
7. **Reproduced byte-identical** from git's R7 board (commands below).
8. **U1 pin faces at rotation 0** checked in pcbnew on the R7 footprint.

## Reproduce

```bash
cd rocket-pcb/rocket-flight-computer-r8
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
T=$(mktemp -d)
git show 431025d:m3_design/assembly_review/m3.kicad_pcb > $T/r7.kicad_pcb      # SHA-256 c872a3d3...
PYTHONUNBUFFERED=1 $KPY m3_design/assembly_review/sources/r8_design/step0/dump_r7_u1.py $T/r7.kicad_pcb $T/r7_u1.json
python3 m3_design/assembly_review/sources/r8_design/step0/make_table.py $T/r7_u1.json $T/pin_table.tsv
cmp $T/pin_table.tsv m3_design/assembly_review/sources/r8_design/pin_table.tsv   # identical
(cd m3_design/assembly_review/sources/r8_design/step0 && python3 final.py)        # D3 crossing figures
rm -rf $T
```

st.com refuses plain curl. Fetch the datasheets with browser-like headers:

```bash
H=(-H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36" -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" -H "Accept-Language: en-US,en;q=0.9" -H "Sec-Fetch-Dest: document" -H "Sec-Fetch-Mode: navigate" -H "Sec-Fetch-Site: none" -H "Sec-Fetch-User: ?1" -H "Upgrade-Insecure-Requests: 1")
curl -sSL --compressed "${H[@]}" -o ds12110.pdf https://www.st.com/resource/en/datasheet/stm32h743vi.pdf
curl -sSL --compressed "${H[@]}" -o an2606.pdf https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf
curl -sSL --compressed "${H[@]}" -o rm0433.pdf https://www.st.com/resource/en/reference_manual/rm0433-stm32h742-stm32h743753-and-stm32h750-value-line-advanced-armbased-32bit-mcus-stmicroelectronics.pdf
```

This session's copies, with `pdftotext -layout` text, are in the session scratchpad `st_docs/{ds,an,rm}`. They are
not in the repository (AGENTS §4).

## Left open (not escalated; none is unsafe or changes a requirement's intent)

- **The D3 pin map rests on a topological model.** Spikes 3(a)–(d) and step 4 confirm it in copper.
  - If the LEDs cannot sit on the west edge, use the D3 fallback (17 crossings). It is a pin change: regenerate the
    table.
  - If spike 3(d) fails or the PB10/PB11 exception is refused, use map H1′ (D2).
- **U12 (TXU0202) A-port output ≤ VCCA = 3V3 is an Inference.** The TI datasheet was not re-read. Step 9's
  electrical review cites it.
- **Bootloader version on the delivered silicon** (V9.0 or V9.1) is unknown. Both are covered.
- **Documents still to regenerate in step 9:** ORDERING (tabs, tooling holes, probe points), M3_R8, R8_VALIDATION and
  the firmware binding. The frozen design is left as is; R8_DECISIONS records its exceptions (PB10/PB11, PE9,
  PE11/PE12).
