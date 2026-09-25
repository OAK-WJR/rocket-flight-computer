# M3-GNSS-R1 / bench firmware v0.7

The GNSS-R1 candidate hash was `7865050b8e2c98e5abe47a0f8092120818505fa6e22acb54162d824024aa6fe6` (not included in this repository; the current board is ASSY-R1, which carries these functions forward). This adds ordinary receiver, logging and diagnostic functions; **no real-board testing, and the complete M3 is not finished**. The old v0.2–v0.6 images keep their historical bindings and cannot be used directly on this candidate.

## Use and delivery

The four images were `build_gnss_inspect`, `build_gnss_record` and their `_query` variants, each with ELF/HEX/BIN, full input / compile-option hashes and the CAD binding. inspect reads flash only; record appends full snapshots with no erase or overwrite; `_query` keeps the one-time camera device-information query, while non-query images keep the camera off. GNSS is an ordinary read-only query, enabled in all four.

No probe was connected, nothing was flashed or ordered. Before installing and powering, confirm the physical board with the board-level bench procedure. The host only opens a serial port the user explicitly provides; it never searches for and auto-selects a device:

```sh
diagnostics/.venv/bin/python -m diagnostics.usb capture \
  --port /dev/cu.YOUR_DEVICE --assembly BOARD_001 \
  --manifest m3_firmware/build_assembly_inspect/manifest.json \
  --out diagnostics/runs/board001_gnss.json

diagnostics/.venv/bin/python -m diagnostics.usb dump \
  --port /dev/cu.YOUR_DEVICE --assembly BOARD_001 \
  --manifest m3_firmware/build_assembly_inspect/manifest.json \
  --sectors 4 --out diagnostics/runs/board001_flash

diagnostics/.venv/bin/python -m diagnostics.storage recover \
  diagnostics/runs/board001_flash/flash.bin \
  --out diagnostics/runs/board001_recovery
```

Use a new output path every time. `--sectors` explicitly limits the download length; it is not an automatic full-flash backup. USB reading, CRC / identity checks and saving partial downloads carry over from v0.6. SWD may only read the same 1024-byte result area; the old SWD flash-map download supports only v5, so use v7's USB download. The UID self-reported by the USB firmware is not independent SWD verification or authentication. The development VID/PID, enumeration / suspend current and real connection still lack compliance acceptance.

## Implementation and evidence

USART6 on PC6/PC7, AF7, 64 MHz HSI kernel clock, BRR 6667, 9600 baud 8N1; configuration and TEACK/REACK verified. The receive IRQ (71) uses a 2048-entry ring buffer storing each byte with its read time; the IRQ handles at most 32 bytes and the main task at most 256 per pass. After a UART error or buffer overflow the untrusted queue is discarded, fault history kept, and the code waits for a complete packet. The loss count is a lower bound: one hardware overrun event can hide several bytes.

Transmission is limited to empty-payload MON-VER and NAV-PVT polls: no CFG writes, receiver resets or dynamic-model settings. At most one poll per second; MON-VER first, then again every ten seconds, with NAV-PVT read in between. Default NMEA is only evidence that bytes / checksums arrive, never a position result. The TX FIFO and TC have 200 ms limits; half-packets time out after 400 ms.

Protocol v7 is still 1024 bytes; words 184..254 are GNSS, word 255 the CRC. It keeps the 92-byte raw NAV-PVT payload, a fixed 40 bytes of MON-VER, and exactly 30 bytes each of the PROTVER/MOD extensions. Other extensions are not in the snapshot, **so it is not a complete serial capture**. Only the checked SPG 5.10, 34.10 and SAM-M10Q identities are recognised; missing or unknown extensions are kept verbatim and marked unconfirmed.

Fix validity checks fixType, gnssFixOK, invalidLlh, coordinate ranges, iTOW and age together. The same iTOW delivered repeatedly does not make an old solution new again; a backwards step, out-of-range values, > 3 s age, a bad checksum or a wrong identity never count as a new fix. The host parses the raw bytes again independently; the horizontal / vertical accuracy fields are only **the receiver's estimate**, never treated as measured error.

M3LG-v1 adds type 3: one 1024-byte snapshot in five pages, three records per sector. Each full snapshot has its own CRC, plus per-page CRC, session / sequence numbers and board / firmware / MCU / flash identity; recovery of the old type-2 512-byte logs is kept. An incomplete record after power loss is never zero-padded or passed off as complete, and earlier complete records remain recoverable. The flash/USB state recorded is a snapshot from before this append, so it cannot claim to include the result of this write.

The regression evidence covered the current binaries, sources, regressions, no-device failure paths and synthetic data: the real production C parser → real C log → Python recovery, byte-by-byte truncation, IRQ/FIFO/clock/CRC/stale-sample/identity errors and old-version regressions. The scripted HAL and synthetic bytes do not model RF, analog supply, real serial noise or real-board power loss. **Bench recording is ~1 Hz and must not be taken as high-rate mission recording or flight validation.**

## References

- [u-blox SAM-M10Q R05](https://content.u-blox.com/sites/default/files/documents/SAM-M10Q_DataSheet_UBX-22013293.pdf): default serial port and pins.
- [M10 SPG 5.10 interface description R03](https://content.u-blox.com/sites/default/files/u-blox-M10-SPG-5.10_InterfaceDescription_UBX-21035062.pdf): MON-VER, NAV-PVT, UBX framing and checksum.
- ST's pinned headers were checked for PC6/PC7 and USART6 IRQ 71; pins were not chosen from general STM32 impressions.
