# M3-PDIAG-R1 bench diagnostics v0.8

v0.8 was bound to the PDIAG-R1 board (SHA256 `83af3097452f3264500560874959e7d425b4db98bdd47b9ec35a6dc36969a28b`, not included in this repository; the current board is ASSY-R1, see `ASSEMBLY_DIAGNOSTICS.md`). It kept GNSS receive, raw sensor bench observation, full flash snapshots and read-only USB download, and added the state and history of four power **inputs**. No actuator control, no real-board testing.

The four images were `build_status_inspect`, `build_status_record` and their `_query` variants. inspect never writes external flash; record appends explicitly with no erase or overwrite; `_query` keeps the one-time camera information query and leaves camera power on; non-query images keep the camera off. Nothing was flashed.

Protocol v8 is still 1024 bytes; the previously reserved words 153..159 became power status: flags, GPIOD IDR, low/high level history, sample tick, last event tick, a lower bound on IRQ invocation count, and the maximum tick interval. USB 160..182 and GNSS 184..254 keep their positions; 127 and 183 stay reserved at zero; 255 is the whole-frame CRC. Storage uses five-page full snapshots; since the old storage structure overlaid the old reserved words 153..155, the power status is copied again before publishing and appending so the diagnostic fields are not cleared.

The inputs are PD0 battery FAULT, PD1 power-select ST, PD4 camera FAULT and PD6 USB FAULT. Pull-ups are in hardware with internal pulls disabled; FAULT lines watch falling edges and ST both edges; the current levels are read by SysTick about every 1 ms. The IRQ does not write flash, reset power or clear chip faults. PRIMASK is preserved across IRQ handling, snapshots are copied in a short critical section, and configuration readback detects changes to input mode, internal pulls and EXTI mapping / enable.

The low 16 history bits mean "was seen low" and the high 16 "was seen high", using only the four bits above. If a FAULT falling edge is already pending, the "was low" evidence is kept even if the level has recovered by the time the ISR reads it. A pending ST cannot tell the edge direction, so no high/low level is invented from the pending bit. History has no clear command; a restart opens a new device / log session.

The IRQ count is a lower bound on handler invocations, **not a pulse count**. Timestamps come from the HAL tick, not an independent real-time clock; masked interrupts, coalescing and pulses before initialisation can be missed, and the maximum tick interval cannot prove there was no wall-clock blind spot. These need an oscilloscope and an independent time reference. The host refuses to draw a normal conclusion from stale / future timestamps, invalid configuration, unknown encodings or history going backwards.

The report can point to which protection branch is abnormal, but a single FAULT alone cannot identify which part failed. FAULT high does not mean power-good. On the TPS2121, ST low means battery (IN2) selected; high means USB (IN1) or output high-impedance, which the host reports as `USB_OR_OUTPUT_HIZ` rather than claiming USB is proven to be supplying. Voltage samples, reset cause and raw fields are kept together; localising further needs instrument measurements.

Only run against a serial port the user has explicitly named:

```sh
diagnostics/.venv/bin/python -m diagnostics.usb capture \
  --port /dev/cu.YOUR_DEVICE --assembly BOARD_001 \
  --manifest m3_firmware/build_status_inspect/manifest.json \
  --out diagnostics/runs/board001_status.json

diagnostics/.venv/bin/python -m diagnostics.usb dump \
  --port /dev/cu.YOUR_DEVICE --assembly BOARD_001 \
  --manifest m3_firmware/build_status_inspect/manifest.json \
  --sectors 4 --out diagnostics/runs/board001_status_flash
```

Use a new output path every time. The download length is set explicitly by `--sectors`; on failure the downloaded prefix is kept, never zero-padded to look successful. The old SWD flash download supports only v5; v8 downloads over USB, and SWD can only read the same 1024-byte result area. Older images cannot be used on this PCB; the development VID/PID, real enumeration / suspend and electrical characteristics still need acceptance.

The regression evidence recorded the hashes of the four ARM binaries, sources and test inputs, covering the production C state machine, scripted register faults through the real HAL adapter, C log → Python recovery, USB simulation and the failure path of a real non-existent serial port. This is **software evidence**, not power, EMC or real-board reliability verification. Whole-board mission and manufacturing-release status: `../STATUS.md`.
