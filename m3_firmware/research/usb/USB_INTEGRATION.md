# USB: rationale and limits

Official documentation was consulted and the pinned sources were read; no paid external search API was used.

## Pinned dependencies

- [TinyUSB 0.21.0 release](https://github.com/hathach/tinyusb/releases/tag/0.21.0), pinned tag source archive SHA256 `b7cdf35c5ccefb0f61640aff94a732ab4ebcb21498201e4a161545891b23ba01`. 251 source / board example / licence files were kept, with per-file hashes. The development APIs were read in the pinned sources before use; nothing depends on the moving master branch.
- [TinyUSB getting started](https://docs.tinyusb.org/en/stable/getting_started.html) requires the application to provide configuration, descriptors and periodic task processing; this project uses the DWC2 device driver and CDC, with no MSC/DFU.
- [ST HAL, pinned commit](https://github.com/STMicroelectronics/stm32h7xx-hal-driver/tree/a1996eed9172b59887bafaaa0ea1816ea14d48b5), the same as the rest of the project. The added MDMA source only satisfies a link dependency of `HAL_QSPI_Abort`; USB and QSPI still run without DMA. All ST files are pinned item by item in `vendor_manifest.json`.
- [pySerial 3.5 official API](https://pyserial.readthedocs.io/en/latest/pyserial_api.html): `Serial(port=None)` does not open immediately; DTR/RTS are set before open; read may return short data; write needs a bounded timeout. Uses an explicit device name, 50 ms read wait, 500 ms write timeout and a 3 s transaction deadline, with no serial_for_url, send_break or 1200-baud reset convention. The wheel comes from a pinned PyPI version with a saved hash.

## Key implementation points actually read

| Pinned source location | Finding | Handling here |
|---|---|---|
| `vendor/tinyusb/hw/bsp/stm32h7/family.c` | The H7 needs the USB clock, PA11/12 AF10, the USB voltage detector and the matching FS controller | The evaluation board's PA9/PA10 configuration was not copied; the real board uses PD15 as an ordinary GPIO |
| `src/portable/synopsys/dwc2/dwc2_stm32.h` | On the H743 RHPORT0 is USB2_OTG_FS; USB DMA cannot access DTCM | DMA 0, slave/FIFO mode; no D-cache |
| `dcd_init` in `src/portable/synopsys/dwc2/dcd_dwc2.c` | With VBUS sensing off it sets a software Bvalid, and connects at the end of initialisation | init is called only after the GPIO has been stably high for 20 ms; disconnect/deinit on unplug |
| The same driver's configuration of `GCCFG.VBDEN` | Dedicated hardware VBUS sensing can be disabled | The unconnected PA9 analog input is not used |
| `device/usbd.c` and the CDC device header | The current API is `tusb_init(rhport, &config)` and `tud_task_ext` | At most 8 events per pass; the task runs in main context; interrupts only queue and dispatch |
| The line-state callback in `class/cdc/cdc_device.c` | DTR changes can notify the application and the FIFO can be cleared | A DTR fall clears application requests / FIFO; an old packet already in the endpoint is still rejected by the host's request ID, so no claim is made that the physical queue is fully cleared |
| ST `hal_rcc_ex` | PLL3 input range 0 is 1..2 MHz, MEDIUM VCO suits 192 MHz, USB can select PLL3Q | HSE 25 / M 25 × N 192 / Q 4 = 48 MHz; silently changing the parent clock of any running PLL is forbidden |
| ST `hal_qspi.c` | Abort / MemoryMapped use handle.Timeout; Abort contains an MDMA branch | SetTimeout 20 ms after initialisation; the official dependency is kept rather than stubbing it with a fake success |

H743-specific GPIO and USB electrical limits refer to [ST DS12110](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf) and [AN4879](https://www.st.com/resource/en/application_note/an4879-introduction-to-usb-hardware-and-pcb-guidelines-using-stm32-mcus-stmicroelectronics.pdf); HAL-derived frequencies or simulations are not treated as real clock measurements.

## Request protocol

A request is 24 bytes, little-endian: `M3RQ`, u16 version 1, u16 operation, u32 request ID, u32 offset, u32 length, CRC32 (of the first 20 bytes). Operation 1 reads the snapshot at fixed offset 0 / length 1024; operation 2 has length 1..1024 with the range entirely inside the 16 MiB flash. Any other operation returns BAD_REQUEST; there are no write / arbitrary-memory commands.

A response is: `M3RS`, u16 version 1, u16 status, u32 request ID, u32 offset, u32 payload length, u32 operation, payload, CRC32 (of everything before). Status 0 = OK; 1 = bad request; 2 = busy; 3 = read failed; error responses have a zero-length payload. At most 1052 bytes; a single pending response provides back-pressure, and partial requests time out after 500 ms. The CRC is the project's existing IEEE CRC32, cross-checked byte by byte and bit by bit against Python's zlib.

The frame CRC provides no authentication, and a UID self-reported over USB cannot replace SWD's independent identity check or a physical part-number check. Every host capture/dump is bound to an explicit manifest; snapshots are allowed while record runs, but host dump only accepts inspect. If the firmware or clock stalls and USB fails, find the cause with SWD and external instruments.

## Not yet proven

No real-board enumeration, real throughput, USB compliance, pre-enumeration / suspend current, real plug / clock-switch faults, complete CDC control-request ordering tests or all-OS verification. DTR is only a protocol session boundary, never treated as an external actuation signal. An RTOS, low power and the watchdog are out of scope; errors never automatically reset the chip, erase the log or retry uncertain transactions.
