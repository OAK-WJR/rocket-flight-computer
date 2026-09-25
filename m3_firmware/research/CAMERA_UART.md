# Camera UART: rationale and limits

Date: 2026-09-08 UTC. M3-UART-R1, an ordinary camera information query; no attitude control or other actuation.

The maker's protocol, the Split 4 manual, ST's pinned drivers and an open-source reference implementation were consulted; no external API key needed.

| Fact | Basis | Use / limit here |
|---|---|---|
| GET_DEVICE_INFO is command 0x00; a request is 0xCC, the command and a CRC; the response is 5 bytes | [RunCam official protocol](https://support.runcam.com/hc/en-us/articles/360014537794-RunCam-Device-Protocol) §1 | The request is fixed at `CC 00 60`. Only the protocol version and 16-bit feature flags are queried; no simulated key presses or setting writes |
| CRC polynomial 0xD5, MSB first, initial value 0 | The CRC implementation at the end of the same official protocol | Production C and the host compute it independently by polynomial long division; the standard check string 123456789 gives 0xBC |
| Features low byte first; protocol 1.0 encoded as 0x01; 115200, no inversion, full duplex | [Betaflight rcdevice.c](https://github.com/betaflight/betaflight/blob/master/src/main/io/rcdevice.c) and [rcdevice.h](https://github.com/betaflight/betaflight/blob/master/src/main/io/rcdevice.h) | Interoperability reference only; none of its driver code copied; no automatic fallback to the old 0x55 protocol. An unknown version keeps the response but is not judged success |
| The Split 4 connects over UART, camera RX to controller TX and vice versa | [Maker's manual](https://www.runcam.com/download/split4k/RC_Split_4k_Manual_EN.pdf) | The manual gives neither complete logic thresholds nor a maximum start-up time, so a software response cannot replace electrical qualification |
| PB10/PB11 USART3 AF7, PC13 = OE, PD3 = power enable | The UART-R1 nine-sheet schematic, board, DS12110 pin table; ST's GPIO AF headers | The build checks physical pin function names, nets, precision divider values and the new interface topology together; old PWR-R3 firmware was not reused with only a hash change |
| The UART clock can be HSI; 8N1, 16× oversampling, prescaler 1 | ST CubeH7 v1.13.0 HAL, pinned commit `a1996eed9172b59887bafaaa0ea1816ea14d48b5` | After setting the USART3 clock source it requires 64 MHz and a BRR readback of 556. The real HSI frequency / drift is not measured |
| HAL polling receive is not a comprehensive error detector | `vendor/hal/Src/stm32h7xx_hal_uart.c`: HAL_UART_Receive and UART_WaitOnFlagUntilTimeout | The adapter checks PE/FE/NE/ORE directly and saves the raw bits before the W1C clear, reading RDR only when RXNE/FIFO is non-empty; FIFO enabled, byte-by-byte polling, no DMA / interrupts |

`fetch_vendor.py` gained 4 matching UART/UARTEx files, 51 vendor files in total; Git tree blobs and SHA-256 were checked and licences kept. UART initialisation, FIFO enable and GPIO APIs were written after reading their real declarations / implementations, not from memory.

## Timing and scope of evidence

At boot the default image first drives PC13/OE low and keeps PD3 power off; it never opens the UART or sends a request. The query image must be built explicitly with `--board uart --camera-query`. It first establishes the MCU TX idle-high level and configures the UART, then powers the camera, waits 3000 ms, enables the interface, drains old receive data with a bound, and sends one device-information query.

The 3000 ms start-up window, the 100 ms transmit / drain limit and the 1000 ms response window are this project's bench settings, **not maker-guaranteed maximum start-up or response times**; adjust them from real measurements. No response can come from a camera not yet ready, an unsupported mode / version, or a supply or wiring problem; it does not prove the device is broken.

Every failure exit of the query function disables OE; with the query enabled, camera power stays on, because the camera may record on its own and the firmware cannot know whether the SD card is being written. It never sends start / stop recording commands. The default image keeps the camera fully off.

Protocol version 3 is still 512 bytes, using the previously reserved words 82..111, with 112..126 zero. The new target rejects old v2 records at the 16-byte header check; the readback tool neither widens the SRAM address range nor adds write permission to target memory. Records keep the first 32 received bytes, the complete valid response, CRC discard count, stale-data count, error bits, GPIO readback and timestamps. A passing CRC proves only the protocol response recorded that time, not voltages, cable immunity or all camera functions.

Software polling uses millisecond deadlines plus a bounded-iteration guard that does not depend on the tick; ST HAL initialisation still depends on a working SysTick. No real watchdog-reset verification was done, so recovery from every clock fault cannot be guaranteed. The single boot-time query result is repeated in diagnostic records and explicitly does not count as several independent communication successes.

## Not yet done

No real board or camera connected; no flashing, logic analyser, supply switching or temperature tests. Camera logic thresholds, U12/U13 power-down isolation, real UART edges, start-up time, protocol support and recording behaviour must be measured. Whole-board IMU samples, flash logging, USB export and full function / reliability acceptance remain open.
