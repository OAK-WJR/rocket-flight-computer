# M3-ASSY-R3 Bench Firmware Implementation Plan (B1–B5)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bench firmware for the R3 board: a read-only diagnostics image v0.9 (all live nets, plug-out self-test) and a separate bench actuation image (servo sweep/stall, buzzer, single 20 ms dummy-load pyro pulse), plus host tools rebound to R3. No flight firmware.

**Architecture:** A new, self-contained R3 build chain (`--board r3`) next to the historical R1 chain, which stays untouched (its inputs are missing and its hash is R1). New logic is pure C (no HAL) tested on the host through ctypes, with thin `*_stm32.c` adapters tested through stub-HAL harnesses — the repository's existing pattern. The actuation code compiles only into the B5 image; the v0.9 image's symbol policy forbids it.

**Tech Stack:** C11, STM32H743 CubeH7 v1.13.0 HAL/LL (vendored), TinyUSB 0.21.0 (vendored), Arm GNU Toolchain 15.2.rel1, Python 3 `unittest` + host clang.

**Spec:** `docs/superpowers/specs/2026-10-05-m3-assy-r3-design.md` (part B)

**Depends on:** the hardware plan completed (Tasks 1–6), because the BOM field edits change the board SHA-256 that the binding pins. Also decide P2 (R125 4.7 k → 3.3 k) and P4 (`PYRO*_GATE_N` rename) first: either changes the hash and the scaling constants below.

## Global Constraints

- Never edit `protocol_assembly.json`, any `build_*` manifest of an older version, or a board hash to make a build pass (AGENTS.md §3).
- Firmware rules from `docs/R2_VERIFICATION.md` §5 and FMEA: first instructions drive PE3, PE4, PE5, PE6 low via BSRR then set them output, lock with `GPIOE->LCKR` and read back bit 16; never enable the TIM1 or TIM15 RCC clocks; never enable trace (PE2–PE6); TIM2 never gets a channel; servos PA0–PA3 low at boot; PA5 low at boot; VLOGIC/V3V3 on ADC3 with the analog switch open; no `HAL_ADCEx_Calibration_Start` (bounded LL calibration pattern of `voltage.c`).
- Thresholds are ratiometric 16-bit codes (VREF+ = 3V3A): `code = mV / 3300 * 65535`. Source: `m3_design/sim_r2/RESULTS.md` §E / `results.json` rows `E.*`, pinned by SHA-256 in the tests.
- Wire format: v9 for the diagnostics image; the B5 image uses its own wire version and manifest `usb_mode: "bench_actuation"`.
- B5 is an owner-approved bench exemption (2026-10-05) from FMEA F-14 / `pyro_may_fire()`: it exists only in its own image, fires only into a dummy load, and is documented as such.

---

### Task 1: Toolchain and reference inputs (B1)

**Files:** Create `m3_firmware/research/r3_inputs.json` (URL + SHA-256 of every reference the R3 build hashes); gitignored `m3_firmware/toolchain/`.

- [ ] Restore every reference PDF the build hashes (IMU, flash, power-status parts, DS12110) from vendor URLs into the gitignored paths and record URL + SHA-256 in `research/r3_inputs.json`; a revised vendor PDF gets a new recorded hash, never a forced old one.
- [ ] Download `https://developer.arm.com/-/media/Files/downloads/gnu/15.2.rel1/binrel/arm-gnu-toolchain-15.2.rel1-darwin-arm64-arm-none-eabi.tar.xz` (141,961,944 bytes) with curl, verify SHA-256 `1938a84b7105c192e3fb4fa5e893ba25f425f7ddab40515ae608cd40f68669a8`, unpack into `m3_firmware/toolchain/`.
- [ ] Run `m3_firmware/toolchain/arm-gnu-toolchain-15.2.rel1-darwin-arm64-arm-none-eabi/bin/arm-none-eabi-gcc --version` — Expected `15.2.1 20251203`.
- [ ] Regenerate `research/usb/tinyusb_manifest.json` from `vendor/tinyusb` (version 0.21.0 from `tusb_option.h`), reviewed.
- [ ] Commit `B1: toolchain pin and R3 reference inputs`.

### Task 2: R3 board binding (B1)

**Files:** Create `m3_design/gate_r3.py` (writes `m3_design/assembly_review/verification_r3.json`), `m3_firmware/r3_binding.py`, `m3_firmware/pins_r3.json`, `m3_firmware/protocol_r3.json`; Modify `m3_firmware/build.py` (add `--board r3`); Test `m3_firmware/test_r3_binding.py`.

**Note:** `pins_r3.json` is defined only here: `pins_status.json` minus PC6/PC7 and `PE3:LED_RED`, plus the `pins_r2.json` additions, plus PB10/PB11, PC13, PA11/PA12, PD15, PD0/PD1/PD4/PD6 and **PE10 = IMU_INT1**; PE3/PE6 go in a separate no-net list checked with `startswith('unconnected-')`.

**Interfaces:** `make_binding() -> dict` with keys `profile='M3-ASSY-R3'`, `board_sha256`, `gnss_fitted=False`, `gnss_dnp=True`, `probes`, `binding_note`.

- [ ] Write failing tests: binding refuses when the PCB hash differs from `verification_r3.json`; refuses when any pin in `pins_r3.json` maps to a different net in `schematic.net.xml`; accepts PE3/PE6 only as `unconnected-…` (no-net list); refuses if U6/C33/C34 or GPS nets exist; checks R124/R125 10k/4.7k, R104/R105 10k/1k, R129/R130, R141/R142, R132/R133, R144/R145 10k/1k, R131/R143 10k.
- [ ] Implement `gate_r3.py` (runs `tools/check.sh` and `check_actuators.py`, hashes all KiCad inputs, writes `ok`, `revision`, `board_sha256`, `inputs_sha256`, results), `pins_r3.json` (from `pins_status.json` minus PC6/PC7 and PE3:LED_RED, plus `pins_r2.json` additions, plus PB10/PB11, PC13, PA11/PA12, PD15, PD0/PD1/PD4/PD6), `r3_binding.py`, `protocol_r3.json` (`board_sha256` copied from the gate output).
- [ ] Run `cd m3_firmware && PYTHONPATH=.. python3 -m unittest test_r3_binding` — PASS. Commit.

### Task 3: Safe-boot block and GPIO roles (B2)

**Files:** Create `m3_firmware/src/safeboot.c/.h`; Modify `src/main.c` (call first, LED_RED → PE8, remove PE3 LED use); Test `tests/safeboot_harness.c`, `test_safeboot.py`.

**Interfaces:** `uint32_t safeboot_apply(void)` returns bitmask of failures (bit0 LCKR not locked, bit1 readback mismatch).

- [ ] Harness test with stub GPIOE/GPIOA/RCC: after `safeboot_apply()`, PE3–PE6 ODR=0 and MODER=output; LCKR bit16 set; PA0–PA3, PA5 output low; RCC TIM1EN/TIM15EN bits never set; returns 0. A stub where LCKR does not latch returns bit0.
- [ ] Implement; run `python3 -m unittest test_safeboot` — PASS. Commit.

### Task 4: ADC1 actuator sense and pull-pin (B2)

**Files:** Create `src/actsense.c/.h` (pure math), `src/actsense_stm32.c` (ADC1: PC0 INP10, PC1 INP11, PC5 INP8, PC4 INP4, PB0 INP9, PB1 INP5), `src/pullpin.c/.h` + `_stm32.c` (PC14 input, latch rule low ≥ 1 s then rising edge); Tests `test_actsense.py`, `tests/actsense_harness.c`, `test_pullpin.py`.

**Interfaces:** `void actsense_convert(const uint16_t raw[6], uint32_t vdda_mv, actsense_mv_t *out)`; `raw_act_mv = raw * vdda_mv * 147 / (47 * 65535)`; `cam5v_mv = raw * vdda_mv * 11 / 65535`.

- [ ] Tests: conversion against hand values (8.4 V → RAW_ACT code at VDDA 3300 = 8.4/3.1277/3.3*65535 ≈ 53 337); ADC1 harness asserts channel order and bounded LL calibration; pull-pin latch timing table.
- [ ] Implement; PASS; commit.

### Task 5: Plug-out self-test classifier (B3)

**Files:** Create `src/selftest.c/.h`; Test `test_selftest.py`.

**Interfaces:** `typedef enum {ST_GOOD=1, ST_OPEN=2, ST_FET_SHORT=3, ST_INCONCLUSIVE=4, ST_NOT_PLUG_OUT=5} st_verdict;` `st_verdict selftest_channel(uint16_t cont_code, uint16_t arm_code, uint16_t raw_act_code, uint8_t raw_act_live);`

Thresholds (ratiometric codes; INFERENCE midpoints of the §E bands, each band ±20 mV error budget → INCONCLUSIVE within 20 mV of a boundary):

```c
#define ST_SHORT_GOOD_CODE   944u   /* 47.6 mV  */
#define ST_GOOD_OPEN_CODE   2389u   /* 120.3 mV */
#define ST_ARM_PLUGIN_CODE  6034u   /* 303.9 mV: above => plug in, refuse self-test */
#define ST_ERR_CODE          397u   /* 20 mV    */
```

- [ ] Tests load `m3_design/sim_r2/results.json` (pin its SHA-256), and for every `E.*` row assert the classifier returns the row's state at min and max; boundary codes ±`ST_ERR_CODE` give `ST_INCONCLUSIVE`; `raw_act_live == 0` with RAW_ACT_SENSE code > 300 mV equivalent gives `ST_NOT_PLUG_OUT` unless RAW_ACT_SENSE reads < 50 mV equivalent (a plugged channel with the rail off back-feeds RAW_ACT to ~215–324 mV, INFERENCE from a DC model; a 300 mV rule would certify a plugged-in channel as plug-out); also require ARM ≈ CONT within ±20 mV and treat CONT > 200 mV as a fault.
- [ ] Implement; PASS; commit.

### Task 6: v0.9 record, protocol and USB (B2)

**Files:** Modify `src/main.c`, `src/storage.h` (decouple 1024-byte kind 3 from `M3_GNSS` via `M3_FULL_RECORD`), `src/usb_descriptors.c` (bcdDevice 0x0009, "v0.9"), `protocol_r3.json` (words 184..254 = R3 block: ADC1 status/errors, six raw codes, RAW_ACT and CAM_5V mV, B3 verdicts, GPIO/LCKR readbacks, pull-pin history, `actuation=0`); remove GNSS from the R3 build (`gnss*.c` not compiled when `--board r3`).
- [ ] `_Static_assert`s on word offsets; host tests: v9 frame decodes; R3 words 0..183 identical to v8 layout; build symbol policy forbids `TIM5`, `TIM8`, `actuate_`, `pyro_` symbols in v0.9.
- [ ] Keep `M3_FULL_RECORD` implied by `-DM3_GNSS` so v7/v8 journals and `GNSSJournalTests` are unchanged.
- [ ] Configure PE10 (IMU_INT1) with the internal pull-down (no pull on the net).
- [ ] Build: `python3 m3_firmware/build.py --board r3 --imu-samples --storage inspect` and `--storage record` — Expected: image + manifest under `build_r3_inspect/`, `build_r3_record/`. Commit.

### Task 7: Host diagnostics rebind (B4)

**Files:** Modify `diagnostics/mailbox.py` (v9 + `M3-ASSY-R3` profile), `storage.py` (version 9), `engine.py` (`gnss_fitted` False path), `triage_rules.py` (drop U6/C33/C34 group for R3), `triage_map.py` (regenerate the test-point map from the R3 PCB; TP85 already exists — add TP120, TP121, TP122, TP123, TP124 because the population check is exact set equality; TP124 is the ground for TP120–TP123), `triage.py`, `triage_report.py`, `engine.py:227-228`, `acquisition.py` (ADC1 words), `transport.py`, `board_binding.json`, `verify_triage.py`; Tests: new `diagnostics/test_r3.py`.
- [ ] Tests: v9 frame + R3 manifest accepted; v9 frame + R1/R2 manifest rejected; v8 frame + R3 manifest rejected; nonzero GNSS-era words in v9 rejected; v2–v8 manifests still decode; triage of a failed RAW_ACT reading points to TP120.
- [ ] `python -m unittest discover -s diagnostics -t . -p 'test_*.py'` — all pass. Commit.

### Task 8: B5 bench actuation image

**Files:** Create `src/bench_act.c/.h` (pure gating state machine), `src/bench_act_stm32.c` (TIM5 servo PWM 333 Hz, TIM8_CH1N buzzer 2.7 kHz, pyro pulse ended by the TIM6 update event in one-pulse mode (TIM6 is a basic timer with no compare channel) at the highest NVIC priority writing `GPIOE->BSRR`, a TIM2 25 ms hard abort (TIM2 never gets an output channel) and a 30 ms backstop), plus a host client `bench_actuation/` (separate from `diagnostics/`, which promises no actuation) that runs arm → confirm and captures CONT/ARM/RAW during the pulse, `src/usb_wire_bench.c` (own wire version, arm/confirm/abort/servo/buzz opcodes); `build.py --board r3 --image bench-act`; Tests `test_bench_act.py`, `tests/bench_act_harness.c`; Doc `m3_firmware/BENCH_ACTUATION.md`.

**Interfaces:** `ba_state ba_step(ba_state s, const ba_inputs *in, ba_event ev, uint32_t now_ms, ba_outputs *out);` refusals: ARM plug not sensed on the requested channel's bus, continuity outside good band, RAW_ACT < 6.6 V, VDDA outside 3.0–3.6 V, gate pull-down test failed, debugger attached, LCKR not locked, other channel not idle, servos not quiet ≥ 200 ms, confirm nonce mismatch or > 5 s after arm. RAW_ACT above ~8.6 V; no B3 plug-out pass this power cycle before the plug was sensed; channel already fired this session; F-14 hazard latch (ARM > 0.4 V before arming → continuous tone, refuse everything). Any USB disconnect/DTR drop/heartbeat loss/timeout → SAFE. Reset → SAFE (no persistence). One pulse per arm. Open owner rulings before any dummy-load fire: single-channel bench ARM plug, confirm window (5 s vs 10 s), stall-hold limits, servo-quiet method, IWDG period, and the F-14/F-6/`pyro_may_fire` exemption written into the FMEA.

- [ ] Tests: each refusal alone blocks; nonce replay/timeout; pulse ends at 20 ms (19–21 ms accepted), wraparound; seeded fuzz invariants (≤ 1 gate high; gate high ⇒ FIRING and all refusals clear; servos idle while firing); harness asserts TIM1/TIM15 never clocked and the termination IRQ has priority 0.
- [ ] v0.9 image symbol check still clean; B5 image contains `ba_step`. Commit.

### Task 9: Docs and PR

- [ ] `m3_firmware/README.md` (v0.9 + B5 images, how to run), `BENCH_ACTUATION.md` (dummy-load procedure, 20× plug-insertion test, servo stall/thermal test, buzzer, instruments, owner exemption), `STATUS.md`, `AGENTS.md` §1 row "R2 firmware" → R3 bench firmware. Open PR with test output.
