# On-board diagnostic log: facts, limits and implementation choices

Pinned source: Winbond W25Q128JV Rev M (2024-12-24), SHA256 `b51bb4303e17a17750c9cbcafc9a776dea842a8971d7cdd5edc70ff738efb1fe`, [maker original](https://www.winbond.com/resource-files/W25Q128JV%20RevM%2012242024%20Plus.pdf). STM32 pins were checked against a cached ST DS12110 Rev 5; that older edition supports only the unchanged pin mapping and does not replace a review of the latest errata. The HAL comes from pinned commit `a1996eed9172b59887bafaaa0ea1816ea14d48b5`, every file and Git blob verified in `vendor_manifest.json`.

| Fact | Location in the original | Constraint in the code |
|---|---|---|
| 16 MiB, 256 B pages, 4 KiB sectors | Winbond §1, 8.2.13/15 | 24-bit addresses, bounds checked on every operation |
| 02h wraps within the page when crossing the page end | 8.2.13, printed p. 36 | Page-aligned only, exactly 256 B, written once, never retried |
| Page Program worst case 3 ms | AC characteristics, tPP | 10 ms budget plus a 12-poll counter; the HAL call itself still depends on SysTick |
| WEL set after WREN and cleared after a successful write; instructions to protected areas may be ignored | 7.1, 8.2.13 | Status before / after the write, 03h byte-by-byte readback, protection settings refused |
| BP/SUS/QE/CMP/WPS bit positions | 7.1, Figures 4a–c | SR1 BP = 0x1c, BUSY/WEL = 3; SR2 SUS = 0x80, CMP = 0x40, QE = 2; SR3 WPS = 4 |
| QE ships as 1 on the IQ variant | 7.1.4 | Record mode requires QE = 1; status registers are never rewritten automatically |
| 6Bh: single-line address, 8 dummies, quad data | 8.2.9, printed p. 31 | Freshly written non-empty structure pages are compared with both 03h and 6Bh; a blank FF read does not prove quad lines |
| 4Bh: 32 dummy clocks then a 64-bit UID | 8.2.26, printed p. 49 | The QSPI dummy field tops out at 31, so a single-line 32-bit alternate-byte phase is used instead of passing 32 to DummyCycles |
| 5Ah with a 24-bit address and 8 dummies reads SFDP | 8.2.28, printed p. 51 | Only the first 8 B are read to check the SFDP signature; no claim of full SFDP parameter-table verification |
| At least 5 ms after power-up before writes | 9.3, tPUW | The driver waits another 6 ms after the existing power-up wait |
| PB2/PD11/PD12/PD13/PE2 are AF9, PB6 is AF10 | ST Tables 10/12/13 | Boot checks every relevant U1/U3 net against the schematic; the scripted HAL verifies pin configuration |
| QSPI FlashSize + 1 is the number of address bits | Pinned HAL QSPI header | FlashSize = 23, single Bank 1, HSI/CLKP 64 MHz ÷ 8 = 8 MHz |

Implementation choices (not maker guarantees): the first 256 B page of each sector stores the board / firmware SHA, MCU UID and flash UID; the remaining 15 pages store five diagnostic records of three pages each, a complete 512 B diagnostic prefix. Each page carries the physical address, the session's first sector, sample number, fragment number, length and CRC32. The host recovers a record only when all three pages are present, numbering / identity agree and the CRC is correct. Records are made after each bench sample (at most 1 Hz); no flight-state decisions or control are implemented.

At boot all 16 MiB are scanned and a new session starts after the highest non-empty sector. Holes are never back-filled, a previous session's partly written sector is never reused, and existing data is never modified. When full or on failure, logging stops while acquisition continues, keeping the error / drop counters. There are no erase, format, unlock, status-register write, flash reset or suspend/resume instructions.

Strict boundaries:

- The NOR must already be correctly erased. An all-FF digital reading does not prove that cells which went through an interrupted erase / program still have normal analog margin. If power is lost before any bit changes, that attempt is indistinguishable from an unused page; the model explicitly allows this unobservable case.
- A CRC is not authentication and does not guarantee zero collisions; whole-page writes are not assumed atomic.
- The test model limits an interruption to the page being programmed. A real supply fault may affect a larger area and must be measured; no physical power-loss verification was done.
- At 1 Hz an empty flash holds 20,480 records in theory, about 5 h 41 min; each reboot skips the remainder of the old session, so real capacity is lower. 500 Hz, continuous FIFO acquisition, bus throughput and fast recovery are unverified.
- A full scan at 8 MHz single-line takes about 16.8 s of raw data time in theory, plus HAL / command / CRC time; wait for SCANNING to finish after boot. This is not a measured boot time.
- inspect uses 03h read-only memory mapping; record uses indirect commands without memory mapping at the same time. Switching modes needs the other firmware installed; this task performed no installation, flashing or chip writes.
- SWD currently reads word by word at 100 kHz, so long log downloads can be slow; USB download was not yet implemented at this version. A download keeps partial files and errors along the way.
- The camera query can be compiled together with recording, but it is still only the device-information query; it does not mean camera recording is implemented.
