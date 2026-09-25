# M3-ASSY-R1 bench diagnostics v0.8.1

This version binds to `m3_design/assembly_review/m3.kicad_pcb`, SHA256 `e432d3436d5029de0a74a4b0ebcd02ec092dedf6d4252ce310f7be301558627f`. After the LED assembly fix it was rebuilt for the exact board ID; production C / headers and GPIO roles are unchanged from v0.8; no flight or actuation functions were added.

| Image directory | External flash | Camera behaviour |
|---|---|---|
| build_assembly_inspect | Read-only check | Off by default |
| build_assembly_record | Explicitly appends diagnostic records, no erase / overwrite | Off by default |
| build_assembly_inspect_query | Read-only check | One information query, then power left on |
| build_assembly_record_query | Explicit append, no erase / overwrite | One information query, then power left on |

All four images provide raw sensor / GNSS bench observation, a 1024-byte snapshot, read-only USB download and power FAULT/ST input history. It is still ~1 Hz bench recording; camera recording, real USB enumeration, and real dynamic supply / RF / environmental performance were not verified by the rebuild. For interpretation of the power status and its sampling limits see [the v0.8 notes](POWER_STATUS_DIAGNOSTICS.md) (its old build directories are historical only).

The host accepts two explicit wire-v8 configurations: M3-PDIAG-R1 and M3-ASSY-R1. It checks the board SHA, build SHA, protocol, CRC and sample times; a matching wire version alone cannot pass a wrong board ID. On disconnect it keeps the failure and the prefix already read, never fabricating normal readings. No physical board or probe was connected and nothing was flashed.

With a confirmed device attached, use a new output path that does not yet exist:

```sh
diagnostics/.venv/bin/python -m diagnostics.usb capture \
  --port /dev/cu.YOUR_DEVICE --assembly BOARD_001 \
  --manifest m3_firmware/build_assembly_inspect/manifest.json \
  --out diagnostics/runs/board001_assembly.json
```

Log export still uses `diagnostics.usb dump` with the same manifest and an explicit `--sectors`. Only run against a device you have specified; verification only opened a randomly generated, non-existent serial path to confirm it returns CONNECTION_FAILED rather than fabricated measurements.

`verify_assembly_firmware.py` re-checks the four ARM binaries, input files and test logs by hash, including old-version compatibility, production C with a scripted HAL, a wrong board ID with the same wire version, fault history, disconnect and no-device tests. All of this is software or file evidence; `hardware_tested`, `flashed` and `full_m3_complete` remain false. (The verification run directory is regenerated locally and is not stored in the repository.)

Re-check with: `diagnostics/.venv/bin/python m3_firmware/verify_assembly_firmware.py`. Any rebuild must first keep the old build, and after any schematic / PCB / footprint change must pass native checks and re-binding again — never edit the manifest by hand to fake compatibility.
